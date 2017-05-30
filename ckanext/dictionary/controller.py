import logging
import ckan.plugins as p
from ckan.lib.base import BaseController
import ckan.lib.helpers as h
from ckan.common import OrderedDict, _, json, request, c, g, response
from paste.deploy.converters import asbool
from urllib import urlencode
import datetime
import mimetypes
import cgi
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.maintain as maintain
import ckan.lib.i18n as i18n
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.lib.datapreview as datapreview
import ckan.lib.plugins
import ckan.lib.uploader as uploader
import ckan.plugins as p
import ckan.lib.render

from ckan.common import config
import ckan.controllers.package as pkgcontroller


log = logging.getLogger(__name__)

pkggg = pkgcontroller.PackageController()


render = base.render
abort = base.abort
redirect = h.redirect_to


NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

get_action = logic.get_action


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]

class DDController(BaseController):
 

    def _setup_template_variables(self, context, data_dict, package_type=None):
        return lookup_package_plugin(package_type).\
            setup_template_variables(context, data_dict)

    def index(self):
	#print(sys.path)
	return p.toolkit.render("base1.html")
    
    def _resource_form(self, package_type):
        # backwards compatibility with plugins not inheriting from
        # DefaultDatasetPlugin and not implmenting resource_form
        plugin = lookup_package_plugin(package_type)
        if hasattr(plugin, 'resource_form'):
            result = plugin.resource_form()
            if result is not None:
                return result
        return lookup_package_plugin().resource_form()


    def _get_package_type(self, id):
        """
        Given the id of a package this method will return the type of the
        package, or 'dataset' if no type is currently set
        """
        pkg = model.Package.get(id)
        if pkg:
            return pkg.type or 'dataset'
        return None

	
    def finaldict(self, data=None, errors=None):

 	from ckan.lib.search import SearchError, SearchQueryError

        package_type = 'dataset'

        try:
            context = {'model': model, 'user': c.user,
                       'auth_user_obj': c.userobj}
            check_access('site_read', context)
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        # unicode format (decoded from utf8)
        q = c.q = request.params.get('q', u'')
        c.query_error = False
        page = h.get_page_number(request.params)

        limit = int(config.get('ckan.datasets_per_page', 20))

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']

        def drill_down_url(alternative_url=None, **by):
            return h.add_url_param(alternative_url=alternative_url,
                                   controller='package', action='search',
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='package', action='search')

        c.remove_field = remove_field

        sort_by = request.params.get('sort', None)
        params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        def _sort_by(fields):
            """
            Sort by the given list of fields.

            Each entry in the list is a 2-tuple: (fieldname, sort_order)

            eg - [('metadata_modified', 'desc'), ('name', 'asc')]

            If fields is empty, then the default ordering is used.
            """
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join('%s %s' % f for f in fields)
                params.append(('sort', sort_string))
            return search_url(params, package_type)

        c.sort_by = _sort_by
        if not sort_by:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            fq = ''
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s:"%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'for_view': True,
                       'auth_user_obj': c.userobj}

            if package_type and package_type != 'dataset':
                # Only show datasets of this particular type
                fq += ' +dataset_type:{type}'.format(type=package_type)
            else:
                # Unless changed via config options, don't show non standard
                # dataset types on the default search page
                if not asbool(
                        config.get('ckan.search.show_all_types', 'False')):
                    fq += ' +dataset_type:dataset'

            facets = OrderedDict()

            default_facet_titles = {
                'organization': _('Organizations'),
                'groups': _('Groups'),
                'tags': _('Tags'),
                'res_format': _('Formats'),
                'license_id': _('Licenses'),
                }

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq.strip(),
                'facet.field': facets.keys(),
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras,
                'include_private': asbool(config.get(
                    'ckan.search.default_include_private', True)),
            }

            query = get_action('package_search')(context, data_dict)
            c.sort_by_selected = query['sort']

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )
            c.search_facets = query['search_facets']
            c.page.items = query['results']
        except SearchQueryError, se:
            # User's search parameters are invalid, in such a way that is not
            # achievable with the web interface, so return a proper error to
            # discourage spiders which are the main cause of this.
            log.info('Dataset search query rejected: %r', se.args)
            abort(400, _('Invalid search query: {error_message}')
                  .format(error_message=str(se)))
        except SearchError, se:
            # May be bad input from the user, but may also be more serious like
            # bad code causing a SOLR syntax error, or a problem connecting to
            # SOLR
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.search_facets = {}
            c.page = h.Page(collection=[])
        c.search_facets_limits = {}
        for facet in c.search_facets.keys():
            try:
                limit = int(request.params.get('_%s_limit' % facet,
                            int(config.get('search.facets.default', 10))))
            except ValueError:
                abort(400, _('Parameter "{parameter_name}" is not '
                             'an integer').format(
                      parameter_name='_%s_limit' % facet))
            c.search_facets_limits[facet] = limit

        self._setup_template_variables(context, {},
                                       package_type=package_type)

#        return render(self._search_template(package_type),
  #                    extra_vars={'dataset_type': package_type})




	variable=''

        if request.method== 'POST':                                           
            print("!!!!!!!!!!!!!!!!!!1 POsted FROM EXTENSION!!!!!!!!!!!1")    
            variable = request.params.get('sel')
        
	c.link = str("/dataset/dictionary/new_dict/"+"prueba")
	return render("package/new_data_dict.html",extra_vars={'package_id':variable})


    def redirectSecond(self, id, data=None, errors=None):
        return render("package/new_resource.html")
   

 def new_data_dictionary(self, id):
        
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!IN THE EXTENTION !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if request.method == 'POST':
            save_action = request.params.get('save')
            print("new data dictionary !!!!!!!!!!!!!!!!")
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}
            counter = 0
            tempdata= ''
            ###########################
            resource_ids = None
            try:
                meta_dict = {'resource_id': '_table_metadata'}
                tables = get_action('datastore_search')(context,meta_dict)
                for t in tables['records']:
                    print(t['name'])
                    if t['name'] == "data_dict":
                        resource_ids = t['alias_of']
            except:
	        resource_ids = None
	    if resource_ids == None:
                create = {'resource':{'package_id':id},'aliases':'data_dict','fields':[{'id':'package_id','type':'text'},{'id':'id','type':'int4'},{'id':'title','type':'text'},{'id':'field_name','type':'text'},{'id':'format','type':'text'},{'id':'description','type':'text'}],'primary_key':['id']}
                get_action('datastore_create')(context,create)
	        print("CREATE TABLE` !!!!!!!!!!!!!!!!!!!!!!!")
                meta_dict = {'resource_id': '_table_metadata'}
                tables = get_action('datastore_search')(context,meta_dict)
                for t in tables['records']:
                    print(t['name'])
                    if t['name'] == "data_dict":
                        resource_ids = t['alias_of']
	    print("PACKAGEID ",id)
            data_dict_dict = {'resource_id': resource_ids,'filters': {'package_id':id},'sort':['id']}

            records=[]
            try:
		print("IM HERE>>>>>>>>>>>>>>>>>>>>>>")
                pkg_data_dictionary = get_action('datastore_search')(context, data_dict_dict)
                records=pkg_data_dictionary['records']
            except NotFound:
                abort(404, _('Dataset not found'))
            except NotAuthorized:
                abort(401, _('Unauthorized to read dataset %s') % id)

            ###########################
            if records==[]:
                data_dict_table = {'resource_id': resource_ids}
                maxID_data = get_action('datastore_search')(context, data_dict_table)
                maxID_records = maxID_data['records']
                maxID = 0
                for record in maxID_records:
        	    print(record['id'])
	            maxID = max(maxID, record['id'])
		print("MAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAX ID: ",maxID)
                while tempdata != None:
                        varNames = ['field_'+str(counter), 'type_'+str(counter), 'description_'+str(counter), 'format_'+str(counter), 'title_'+str(counter),]
                        tempdata = request.params.get(varNames[0])
                        datafield = request.params.get(varNames[0])
                        datatype = request.params.get(varNames[1])
                        datadesc = request.params.get(varNames[2])
                        dataformat = request.params.get(varNames[3])
                        datatitle = request.params.get(varNames[4])
                        tdata = {'resource_id':resource_ids, 'records':[{'package_id' : id, 'field_name':datafield, 'description':datadesc, "title":datatitle, "format":dataformat, 'id' : maxID+counter+1}], 'method': 'upsert'}
                        print("datafield: ",datafield," datatype: ",datatype," datadesc: ",datadesc)
                        if datafield!=None or datatype!=None or datadesc!=None or datatitle!=None or dataformat!=None:
                                if datafield!='' or datatype!='' or datadesc!='' or datatitle!='' or dataformat!='':
                                        get_action('datastore_upsert')(context,  tdata)
                        print(tempdata)
                        counter = counter +1
            else:
                 data_dict_table = {'resource_id': resource_ids}
                 maxID_data = get_action('datastore_search')(context, data_dict_table)
                 maxID_records = maxID_data['records']
                 maxID = 0
                 for record in maxID_records:
		        print(record['id'])
                        maxID = max(maxID, record['id']+0)
		 print(maxID)
                 #counter=0
                 #countHelper='field_'+str(counter)
                 #idHelper='id_'+str(counter)
                 #editedIds=[]
                 #tempdata=tempdata=request.params.get(countHelper)
                 #while tempdata != None:
                 #       varNames = ['field_'+str(counter), 'type_'+str(counter), 'description_'+str(counter), 'sensitivity_'+str(counter), 'id_'+str(counter)]
                 #       print("ID: ",request.params.get(idHelper))
                 #       editedIds.append(request.params.get(idHelper))
                 #       counter+=1
                 #       countHelper='field_'+str(counter)
                 #       idHelper='id_'+str(counter)
                 #       print("CONUTHELPER: ",countHelper)
                 #       print("TEMPDATA: ",tempdata)

                 #       tempdata=request.params.get(countHelper)
                 #print("PRIMARY KEYS ARE: ",editedIds)
                 #tempdata= ''
                 addCounter=1
                 while tempdata != None:
                        varNames = ['field_'+str(counter), 'type_'+str(counter), 'description_'+str(counter), 'title_'+str(counter), 'format_'+str(counter), 'id_'+str(counter)]
                        tempdata = request.params.get(varNames[0])
                        datafield = request.params.get(varNames[0])
                        datatype = request.params.get(varNames[1])
                        datadesc = request.params.get(varNames[2])
                        datatitle =request.params.get(varNames[3])
                        dataformat = request.params.get(varNames[4])
                        dataid = request.params.get(varNames[5])
                        tdata = {'resource_id':resource_ids, 'records':[{'package_id' : id, 'field_name':datafield, 'description':datadesc, "title":datatitle, "format": dataformat,"id":dataid}], 'method': 'update','force':True}
                        #print("datafield: ",datafield," datatype: ",datatype," datadesc: ",datadesc," datasens: ",datasens," dataiid: ",dataid)
			if datafield!=None or datatype!=None or datadesc!=None or datatitle!= None or dataformat!=None:
                                if datafield!='' or datatype!='' or datadesc!='' or datatitle!='' or dataformat!='':
                                     #print("FOUR VAUES NOT BLANK")
                                     if dataid!='' and dataid!=None:
                                        #print("FOUR VALUES NOT BLANK AND ID EXISTS ",dataid)
                                        get_action('datastore_upsert')(context,  tdata)
                                     else:
                                        tdata1 = {'resource_id':resource_ids, 'records':[{'package_id' : id, 'field_name':datafield, 'description':datadesc, "title":datatitle, "format":dataformat,'id' : maxID+addCounter}], 'method': 'insert'}
                                        print("uperst !!!!!!!!" + datatitle + str(maxID))
				        get_action('datastore_upsert')(context,  tdata1)
				        print("success")
                                        addCounter+=1
                                else:
                                     #print("FOUR VALUES BLANK")
                                     req={'resource_id':resource_ids,'filters': {'id':dataid}}
                                     get_action('datastore_delete')(context, req)
                        print(tempdata)
                        counter = counter +1

            #data = request.params

            sel = request.params.get('sel')
            
            if save_action == 'go-add-dict':
                context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}
                data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            elif save_action == 'go-dataset-new': #cambio aqui
		#redirect(h.url_for(str('/dataset/edit/prueba')))                
		redirect(h.url_for(controller="package", action="new")) #cambio aqui new por edit y agregue el id = pgk_name

        #print("!!!!!!!!!!! the value of temp is",temp, id)
        print("!!!!!!!!!!!!")
        redirect(h.url_for(controller='package', action='read', id=id))


################################################################
 
 
#Agregando para pruebas


#######################################################################



    def new_data_dictionary_dos(self):
        if request.method == 'POST':
            save_action = request.params.get('save')        
            sel = ""
            sel = request.params.get('selecting_schemas')

            if save_action == 'go-dataset-new':        
                package_type = self._get_package_type(sel)
                context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

                #if context['save'] and not data:
                #    return self._save_edit(sel, context, package_type=package_type)
                try:
                    c.pkg_dict = get_action('package_show')(dict(context,
                                                         for_view=True),
                                                    {'id': sel})
                    context['for_edit'] = True
                    old_data = get_action('package_show')(context, {'id': sel})
                    # old data is from the database and data is passed from the
                    # user if there is a validation error. Use users data if there.
                    #if data:
                    #    old_data.update(data)
                    data = old_data
                except (NotFound, NotAuthorized):
                    abort(404, _('Dataset not found'))
		            
                c.form_action = h.url_for(controller='package', action='new')
                c.form_style = 'new'

		#cleaning main dataset parameters 		
		data['id']=""
              	data['name']=""
		data['title']=""
		data['url']=""
		return pkggg.new(data=data, errors=None, error_summary=None)
            
            elif save_action == 'go-dataset-skip':
		redirect(h.url_for(controller='package', action='new'))
		










