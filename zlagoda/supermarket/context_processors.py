from . import db_utils as db

def user_role(request):
    if request.user.is_authenticated:
        emp_list = db.get_employee_by_id(request.user.username)
        if emp_list:
            return {'role': emp_list[0]['empl_role']}
    return {'role': ''}