from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

STEPS = [
    ('intake', "Intake"),
    ('drawing', "Ontwerp"),
    ('validation', "Uw goedkeuring"),
    ('production', "Productie"),
    ('installation', "Plaatsing"),
]
STEP_INDEX = {
    'intake': 0, 'drawing': 1, 'validation': 2, 'prep': 3, 'sawing': 3, 'cnc': 3,
    'assembly': 4, 'delivered': 5,
}


class McInterieurPortal(CustomerPortal):

    def _prepare_portal_counter_values(self, counter):
        if counter == 'mc_project_count':
            return 'mc.project', [], 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route(['/my/interieur', '/my/interieur/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_mc_projects(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        Project = request.env['mc.project']
        domain = []
        count = Project.search_count(domain)
        pager = portal_pager(url='/my/interieur', total=count, page=page, step=self._items_per_page)
        projects = Project.search(domain, order='id desc', limit=self._items_per_page, offset=pager['offset'])
        request.session['my_mc_projects_history'] = projects.ids[:100]
        values.update({
            'projects': projects,
            'page_name': 'mc_project',
            'default_url': '/my/interieur',
            'pager': pager,
        })
        return request.render('mc_interieur.portal_my_mc_projects', values)

    def _mc_get_project(self, project_id, access_token=None):
        return self._document_check_access('mc.project', project_id, access_token=access_token)

    @http.route(['/my/interieur/<int:project_id>'], type='http', auth='public', website=True)
    def portal_my_mc_project(self, project_id, access_token=None, message=None, error=None, **kw):
        try:
            project_sudo = self._mc_get_project(project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        version = project_sudo.version_ids.filtered(lambda v: v.state != 'draft').sorted('number')[-1:]
        quote = version.sale_order_id if version else request.env['sale.order']
        values = self._prepare_portal_layout_values()
        values.update({
            'project': project_sudo,
            'version': version,
            'quote': quote,
            'versions': project_sudo.version_ids.filtered(lambda v: v.state != 'draft').sorted('number', reverse=True),
            'questions': project_sudo.question_ids.filtered('to_customer'),
            'open_questions': project_sudo.question_ids.filtered(lambda q: q.to_customer and not q.done),
            'steps': STEPS,
            'current_step': STEP_INDEX.get(project_sudo.stage, 0),
            'page_name': 'mc_project',
            'access_token': access_token,
            'message': message,
            'error': error,
        })
        values = self._get_page_view_values(
            project_sudo, access_token, values, 'my_mc_projects_history', False, **kw)
        return request.render('mc_interieur.portal_my_mc_project', values)

    def _mc_redirect(self, project_sudo, access_token, **params):
        query = '&'.join(f'{key}={value}' for key, value in params.items() if value)
        token = f'access_token={access_token}' if access_token else ''
        separator = '&' if token and query else ''
        suffix = f'?{token}{separator}{query}' if token or query else ''
        return request.redirect(f'/my/interieur/{project_sudo.id}{suffix}')

    @http.route(['/my/interieur/<int:project_id>/answer'], type='http', auth='public', methods=['POST'], website=True)
    def portal_mc_answer(self, project_id, question_id=None, answer=None, access_token=None, **kw):
        try:
            project_sudo = self._mc_get_project(project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        question = project_sudo.question_ids.filtered(
            lambda q: q.id == int(question_id or 0) and q.to_customer and not q.done)
        if question and (answer or '').strip():
            question._mc_customer_answer(answer.strip())
            return self._mc_redirect(project_sudo, access_token, message='answered')
        return self._mc_redirect(project_sudo, access_token, error='empty_answer')

    @http.route(['/my/interieur/<int:project_id>/approve'], type='http', auth='public', methods=['POST'], website=True)
    def portal_mc_approve(self, project_id, signer_name=None, confirm=None, access_token=None, **kw):
        try:
            project_sudo = self._mc_get_project(project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        version = project_sudo.version_ids.filtered(lambda v: v.state == 'pending')[:1]
        if not version:
            return self._mc_redirect(project_sudo, access_token, error='not_pending')
        if project_sudo.customer_question_count:
            return self._mc_redirect(project_sudo, access_token, error='open_questions')
        if not confirm or not (signer_name or '').strip():
            return self._mc_redirect(project_sudo, access_token, error='missing_signature')
        try:
            version._mc_customer_approve(signer_name)
        except UserError:
            return self._mc_redirect(project_sudo, access_token, error='not_pending')
        return self._mc_redirect(project_sudo, access_token, message='approved')

    @http.route(['/my/interieur/<int:project_id>/changes'], type='http', auth='public', methods=['POST'], website=True)
    def portal_mc_changes(self, project_id, remarks=None, access_token=None, **kw):
        try:
            project_sudo = self._mc_get_project(project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        version = project_sudo.version_ids.filtered(lambda v: v.state == 'pending')[:1]
        if not version:
            return self._mc_redirect(project_sudo, access_token, error='not_pending')
        if not (remarks or '').strip():
            return self._mc_redirect(project_sudo, access_token, error='empty_remarks')
        version._mc_customer_request_changes(remarks)
        return self._mc_redirect(project_sudo, access_token, message='changes_sent')
