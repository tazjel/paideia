# coding: utf8

if 0:
    from gluon import current, URL
    auth = current.auth
    db = current.db
    request = current.request
from paideia_bugs import Bug
from applications.paideia.modules.paideia_utils import simple_obj_print

@auth.requires_membership(role='administrators')
def listing():
    return dict()

@auth.requires_membership(role='administrators')
def undo_bug():
    '''
    Controller to receive ajax signal and trigger the Bug class method to undo
    the effects of a reported bug on the user's performance record.
    '''
    b = Bug(request.vars.step, request.vars.in_path, request.vars.map_location)
    u = b.undo(request.vars.id, request.vars.log_id, float(request.vars.score),
               request.vars.bug_status, request.vars.user_name,
               request.vars.admin_comment)
    return u

@auth.requires_membership(role='administrators')
def sil():
    """ """
    response = current.response
        # Scripts for charts
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/d3/3.4.10/d3.min.js')
    response.files.append(URL('static', 'js/user_stats.js'))

    # Include files for Datatables jquery plugin and bootstrap css styling
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables/1.10.0/'
                          'js/jquery.dataTables.min.js')
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables-colvis/1.1.0/'
                          'js/datatables.colvis.min.js')
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables-colvis/1.1.0/'
                          'css/datatables.colvis.min.css')
    response.files.append("https://cdn.datatables.net/fixedcolumns/3.0.1/js/"
                          "dataTables.fixedColumns.min.js")  # fixedColumns plugin
    response.files.append("https://cdn.datatables.net/fixedcolumns/3.0.1/css/"
                          "dataTables.fixedColumns.css")  # fixedColumns plugin css
    response.files.append("https://cdn.datatables.net/plug-ins/28e7751dbec/"
                          "integration/bootstrap/3/dataTables.bootstrap.css")  # bootstrap css

    steps_inactive_locations_data = db(db.steps_inactive_locations.id > 0).select(db.steps_inactive_locations.ALL,orderby=db.steps_inactive_locations.step_id).as_list()
    #simple_obj_print(steps_inactive_locations_data, "steps_inactive_locations_data")
    return {'steps_inactive_locations_data': steps_inactive_locations_data}
