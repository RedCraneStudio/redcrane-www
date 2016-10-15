import redcrane.app, getpass
from redcrane.models import User

while 1:
    # get input
    cmd = raw_input('> ')

    # reset variables
    user = None

    # sign up
    if cmd == 'signup':
        while 1:
            username = raw_input('Username: ')
            email = raw_input('Email: ')
            password = getpass.getpass('Password: ')
            confirm_password = getpass.getpass('Confirm password: ')

            if confirm_password == password:
                try:
                    new_user = User(username=username, password=password, email=email)
                    new_user.save()
                    break
                except Exception as e:
                    print 'Error: %s' % e
                    pass
            else:
                print 'Passwords do not match!'
                pass

        print 'User %s created on %s' % (new_user.username, new_user.created_at)
        print 'I wont email you. Promise.'

    # list users
    if cmd == 'list users':
        for users in User.objects.all():
            print '''
                %s:
                    - account created ~ %s
                    - email ~ %s
            ''' % (users.username, users.created_at, users.email)

    # delete user
    try:
        user = cmd.split('delete user ', 1)[1]
        ans = raw_input('Are you sure you want to delete this user [Y/N]\r\n')

        if ans.lower() == 'y':
            User.objects(username=user).delete()
            print 'Deleted user %s.' % user
        else:
            print 'Did not delete user %s.' % user
            pass
    except:
        if user != None:
            print 'User with the name %s likely does not exist.' %user
        else:
            pass

    # help
    if cmd == 'help':
        print '''
            Available commands:
                - signup ~ sign up for an account
                - list users ~ lists all users
                - delete user [username] ~ deletes a user
                - exit ~ exits script
        '''

    # exit
    if cmd == 'exit':
        break
        exit()
