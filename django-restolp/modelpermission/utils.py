from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q

class BaseModelLevelPermissions:
    def __init__(self):
        self.USER_MODEL = get_user_model()
    
    def get_permissions(
            self, 
            permission_level : int, 
            content_type : object
        ) -> list:
        '''
            get permissions according to permission level
        '''
        if permission_level == 1:
            permissions = Permission.objects.filter(
                content_type=content_type.id,
                codename__icontains='view'
            )
        elif permission_level == 2:
            permissions = Permission.objects.filter(
                Q(codename__icontains='view', content_type=content_type.id) | 
                Q(codename__icontains='add', content_type=content_type.id)
            )
        elif permission_level == 3:
            permissions = Permission.objects.filter(
                Q(codename__icontains='view', content_type=content_type.id) | 
                Q(codename__icontains='add', content_type=content_type.id) | 
                Q(codename__icontains='change', content_type=content_type.id)
            )
        elif permission_level == 4:
            permissions = Permission.objects.filter(
                content_type=content_type.id
            )
        else:
            raise Exception('You should provide permission level')
        return permissions


class UserModelLevelPermissions(BaseModelLevelPermissions):
    '''
    This class provides model level permissions for user
    '''
    def get_user_permissions(self, user : object) -> dict:
        '''
            get specific user's all permissions
        '''
        user_permissions = []
        for permission in user.user_permissions.all():
            data = {
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
                'content_type': permission.content_type.id
            }
            user_permissions.append(data)
        result = {
            'result' : user_permissions
        }
        return result
    
    def get_all_user_permissions(self) -> list:
        '''
            get all users permissions
        '''
        users = self.USER_MODEL.objects.all()
        users_permissions = []
        for user in users:
            user_permissions = []
            for permission in user.user_permissions.all():
                data = {
                    'id': permission.id,
                    'name': permission.name,
                    'codename': permission.codename,
                    'content_type': permission.content_type.id
                }
                user_permissions.append(data)
            data = {
                'user': user.username,
                'permissions': user_permissions
            }
            users_permissions.append(data)
        result = {
            'result' : users_permissions
        }
        return result

    def create_group_or_assgin_user(
        self, 
        group : Group | str,
        user : object | None = None,
        both : bool = False 
        ) -> None:
        '''
            create new group, assign user to group or both
            if user is None, create new group
            if user is not None but group is None, create new group and assign user to group
            if both is True, create new group and assign user to group
        '''
        if user is None and isinstance(group,  str):
            group = Group.objects.create(name=group)
        elif user is not None and group is None:
            raise Exception('You should provide group name')
        elif user is None and isinstance(group, Group):
            raise Exception('You should provide user')
        elif (user is not None and isinstance(group, str)) and (both is True):
            group = Group.objects.create(name=group)
            user.groups.add(group)
        elif user is not None and isinstance(group, Group):
            user.groups.add(group)

    def set_user_permission_api(
            self, 
            user : int, 
            permission : list, 
            ) -> list | None :
        '''
            set model level permission to user with api
            user can be int 
            permission: list of permission id
        '''
        print(user, permission)
        if isinstance(user, int) and isinstance(permission, list):
            # we should convert to int because its come as string
            user = get_user_model().objects.get(id=int(user))
            permission = [int(p) for p in permission]
            user.user_permissions.set(permission)
            perms = []
            for p in user.user_permissions.all():
                data = {
                    'id': p.id,
                    'name': p.name,
                    'codename': p.codename
                }
                perms.append(data)
            return perms
        elif user is None:
            raise Exception('You should provide user')
        elif permission is None or permission is not list:
            raise Exception('You should provide permission or permission should be list')

    def set_user_permission(
            self, 
            user : object | str | list, 
            permission_level : int, 
            model : object | str,
            app_label : str) -> None:
        '''
            set model level permission to user
            user can be instance of user model or username or list of username
            permission_level;
                1: view
                2: view, add
                3: view, add, change
                4: view, add, change, delete
            model: model name or instance of model
            app_label: app name
        '''
        # get user 
        if isinstance(user, str):
            user = [self.USER_MODEL.objects.get(username=user)]
        elif isinstance(user, list):
            user_list = []
            for username in user:
                usr = self.USER_MODEL.objects.get(username=username)
                user_list.append(usr)
            user = user_list
        elif isinstance(user, self.USER_MODEL):
            user = [user]
        else:
            raise Exception('You should provide user or username or list of username')
        
        # get content type of model
        if isinstance(model, str):
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model.lower())
            except ContentType.DoesNotExist:
                raise Exception('Model does not exist')
        elif isinstance(model, object):
            try:
                content_type = ContentType.objects.get_for_model(model)
            except ContentType.DoesNotExist:
                raise Exception('Model does not exist')
        else:
            raise Exception('You should provide model or model name')
        
        # get permissions according to permission level
        permissions = self.get_permissions(permission_level, content_type)

        # assign permissions to user
        try:
            for u in user:
                u.user_permissions.set(permissions) 
        except Exception as e:
            raise Exception(e)

   
class GroupModelLevelPermission(BaseModelLevelPermissions):
    '''
    This class provides model level permissions for group
    '''
    def set_group_permission(
            self, 
            group : Group | str, 
            permission_level : int, 
            model : object | str,
            app_label : str) -> None:
        '''
            set model level permission to group
            group can be instance of group model or group name
            permission_level;
                1: view
                2: view, add
                3: view, add, change
                4: view, add, change, delete
            model: model name or instance of model
            app_label: app name
        '''
        # get group 
        if isinstance(group, str):
            try:
                group = Group.objects.get(name=group)
            except Group.DoesNotExist:
                raise Exception('Group does not exist')
        elif isinstance(group, Group):
            group = group
        else:
            raise Exception('You should provide group or group name')
        
        # get content type of model
        if isinstance(model, str):
            try:
                content_type = ContentType.objects.get(app_label=app_label.lower(), model=model.lower())
            except ContentType.DoesNotExist:
                raise Exception('Model does not exist')
        elif isinstance(model, object):
            try:
                content_type = ContentType.objects.get_for_model(model)
            except ContentType.DoesNotExist:
                raise Exception('Model does not exist')
        else:
            raise Exception('You should provide model or model name')
        
        # get permissions according to permission level
        permissions = self.get_permissions(permission_level, content_type)

        
        # assign permissions to group
        try:
            group.permissions.set(permissions)
        except Exception as e:
            raise Exception(e)

    def set_group_permission_api(
            self, 
            group : int, 
            permission : list, 
            ) -> list | None :
        '''
            set model level permission to group with api
            group can be int 
            permission: list of permission id
        '''
        if isinstance(group, int) and isinstance(permission, list):
            # we should convert to int because its come as string
            group = Group.objects.get(id=int(group))
            permission = [int(p) for p in permission]
            group.permissions.set(permission)
            perms = []
            for p in group.permissions.all():
                data = {
                    'id': p.id,
                    'name': p.name,
                    'codename': p.codename
                }
                perms.append(data)
            return perms
        elif group is None:
            raise Exception('You should provide group')
        elif permission is None or permission is not list:
            raise Exception('You should provide permission or permission should be list')
        
    def get_all_group_permissions(self) -> list:
        '''
            get all groups permissions
        '''
        groups = Group.objects.all()
        groups_permissions = []
        for group in groups:
            group_permissions = []
            for permission in group.permissions.all():
                data = {
                    'id': permission.id,
                    'name': permission.name,
                    'codename': permission.codename,
                    'content_type': permission.content_type.id
                }
                group_permissions.append(data)
            data = {
                'group': group.name,
                'permissions': group_permissions
            }
            groups_permissions.append(data)
        result = {
            'result' : groups_permissions
        }
        return result
    
    def get_group_permissions(self, group : Group) -> dict:
        '''
            get specific group's all permissions
        '''
        group_permissions = []
        for permissions in group.permissions.all():
            data = {
                'id': permissions.id,
                'name': permissions.name,
                'codename': permissions.codename,
                'content_type': permissions.content_type.id
            }
            group_permissions.append(data)
        result = {
            'permissions' : group_permissions
        }
        return result