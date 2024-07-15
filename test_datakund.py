from linkedin_api import Linkedin


if __name__ == '__main__':
    # Authenticate using any Linked in account credentials
    api = Linkedin('gtoravane@gmail,com', 'Kenta@147')

    # GET a profile
    profile = api.get_profile('billy-g')

    # GET a profiles contact info
    contact_info = api.get_profile_contact_info('billy-g')

    # GET 1st degree connections of a given profile
    connections = api.get_profile_connections('1234asc12304')

    print(connections)
