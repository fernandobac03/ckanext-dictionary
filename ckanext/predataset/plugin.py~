import ckan.plugins as p


class Pre_AddDatasetPlugin(p.SingletonPlugin):
    '''Selection of a dataset prior to the creation of a new dataset with autocompleted fields'''

    p.implements(p.IRoutes,inherit=True)
    p.implements(p.IConfigurer)

    def before_map(self, map):
 	
	map.connect('add dataset new form', '/dataset/new_form',controller='ckanext.pre-addataset.controller:DDController', action='schema_select')    

	map.connect('add dataset', '/dataset/new_dataset',controller='ckanext.pre-addataset.controller:DDController', action='new_dataset')          
 	
        return map

    def after_map(self, map):
	
	map.connect('add dataset new form', '/dataset/new_form',controller='ckanext.pre-addataset.controller:DDController', action='schema_select')       
	
	map.connect('add dataset', '/dataset/new_dataset',controller='ckanext.pre-addataset.controller:DDController', action='new_dataset')   

        return map



    def update_config(self, config_):
        p.toolkit.add_template_directory(config_, 'templates')
        p.toolkit.add_public_directory(config_, 'public')
        p.toolkit.add_resource('fanstatic', 'dictionary')
