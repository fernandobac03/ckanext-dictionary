import ckan.plugins as p


class Data_DictionaryPlugin(p.SingletonPlugin):
    '''data dictionary plugin.'''

    p.implements(p.IRoutes,inherit=True)
    p.implements(p.IConfigurer)

    #def update_config(self, config):
        #p.toolkit.add_template_directory(config, 'templates')
        #p.toolkit.add_resource('public/ckanext/stats', 'ckanext_stats')


    def before_map(self, map):
 	map.connect('add dataset new form', '/dataset/new_form',controller='ckanext.dictionary.controller:DDController', action='schema_select')    

	map.connect('add dataset', '/dataset/new_inia',controller='ckanext.dictionary.controller:DDController', action='new_data_dictionary_dos')          
 	
	#map.connect(' temp', '/demp/demo',
         #   controller='ckanext.dictionary.controller:DDController',
        #    action='index')

#        map.connect('data_dict_add','/dataset/dictionary/add/{id}',
#		controller='ckanext.dictionary.controller:DDController',
#		action='finaldict') # was /dataset/dictionary/edit/{id}'

#	map.connect('dataset_edit_dictionary','/dataset/dictionary/edit/{id}',
#		controller='ckanext.dictionary.controller:DDController',
#                action='edit_dictionary', ckan_icon='edit')

#	#map.connect('/dataset/new_resource/{id}',controller='ckanext.dictionary.controller:DDController', action='new_resource_ext') documentado por fernando
#	#m.connect('Intermediate post', '/dataset/dictionary/capstonePost', action='testPost')

#	map.connect('data dict button','/dataset/dictionary/new_dict/{id}',
#		controller='ckanext.dictionary.controller:DDController',
#                action="new_data_dictionary")

#	#map.connect('add dataDictionary', '/dataset/dictionary/capstone',
#	#	controller='ckanext.dictionary.controller:DDController',
#        #        action='addDictionary')

#	map.connect('dataset_dictionary', '/dataset/dictionary/{id}',
#		controller='ckanext.dictionary.controller:DDController',
#                action='dictionary', ckan_icon='info-sign')

#        #map.connect('stats_action', '/stats/{action}',
#            #controller='ckanext.stats.controller:StatsController')
        return map

    def after_map(self, map):
	map.connect('add dataset new form', '/dataset/new_form',controller='ckanext.dictionary.controller:DDController', action='schema_select')       
	
	map.connect('add dataset', '/dataset/new_inia',controller='ckanext.dictionary.controller:DDController', action='new_data_dictionary_dos')   

#        map.connect(' temp', '/demp/demo',
#            controller='ckanext.dictionary.controller:DDController',
#            action='index')

#        map.connect('data_dict_add','/dataset/dictionary/add/{id}',
#                controller='ckanext.dictionary.controller:DDController',
#                action='finaldict') # was /dataset/dictionary/edit/{id}'

#        map.connect('dataset_edit_dictionary','/dataset/dictionary/edit/{id}',
#                controller='ckanext.dictionary.controller:DDController',
#                action='edit_dictionary', ckan_icon='edit')

#       # map.connect('/dataset/new_resource/{id}',controller='ckanext.dictionary.controller:DDController', action='new_resource_ext') documentado por fernando
#        #m.connect('Intermediate post', '/dataset/dictionary/capstonePost', action='testPost')
#        #map.connect('data dict button','/dataset/dictionary/new_dict/{id}',
#        #       controller='ckanext.dictionary.controller:DDController',
#        #        action="new_data_dictionary")
#        #map.connect('add dataDictionary', '/dataset/dictionary/capstone',
#        #       controller='ckanext.dictionary.controller:DDController',
#        #        action='addDictionary')

#        map.connect('dataset_dictionary', '/dataset/dictionary/{id}',
#                controller='ckanext.dictionary.controller:DDController',
#                action='dictionary', ckan_icon='info-sign')

#        #map.connect('stats_action', '/stats/{action}',
#            #controller='ckanext.stats.controller:StatsController')
        return map



    def update_config(self, config_):
        p.toolkit.add_template_directory(config_, 'templates')
        p.toolkit.add_public_directory(config_, 'public')
        p.toolkit.add_resource('fanstatic', 'dictionary')
