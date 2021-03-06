from flask import Blueprint, current_app, redirect, request, url_for, session
import requests

from backend.extensions import oauth


auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')


def debugging_compliance_fix(session):
    def _fix(response):
        current_app.logger.info('access_token request url: %s', response.request.url)
        current_app.logger.info('access_token request headers: %s', response.request.headers)
        current_app.logger.info('access_token request body: %s', response.request.body)
        current_app.logger.info('access_token response: %s', response)
        current_app.logger.info('access_token response.status_code: %s', response.status_code)
        current_app.logger.info('access_token response.content: %s', response.content)

        response.raise_for_status()

        return response
    session.register_compliance_hook('access_token_response', _fix)


@auth_blueprint.route('/launch')
def launch():
    """
    SMART-on-FHIR launch endpoint
    set /auth/launch as SoF App Launch URL
    """
    iss = request.args['iss']
    current_app.logger.debug('iss from EHR: %s', iss)
    session.setdefault('iss', iss)

    launch = request.args.get('launch')
    if launch:
        # launch value recieved from EHR
        current_app.logger.debug('launch: %s', launch)


    # errors with r4 even if iss and aud params match
    #iss = 'https://launch.smarthealthit.org/v/r2/fhir'

    # fetch conformance statement from /metadata
    ehr_metadata_url = '%s/metadata' % iss
    metadata = requests.get(
        ehr_metadata_url,
        headers={'Accept': 'application/json'},
    )
    metadata.raise_for_status()
    metadata_security = metadata.json()['rest'][0]['security']

    # todo: use less fragile lookup logic (JSONPath?)
    authorize_url = metadata_security['extension'][0]['extension'][0]['valueUri']
    token_url = metadata_security['extension'][0]['extension'][1]['valueUri']

    # set client id and secret from flask config
    oauth.register(
        name='sof',
        access_token_url=token_url,
        authorize_url=authorize_url,
        compliance_fix=debugging_compliance_fix,
        # todo: try using iss
        #api_base_url=iss+'/',
        client_kwargs={'scope': current_app.config['SOF_CLIENT_SCOPES']},
    )
    # work around back-end caching of dynamic config values
    oauth.sof.authorize_url = authorize_url
    oauth.sof.access_token_url = token_url

    # URL to pass (as QS param) to EHR Authz server
    # EHR Authz server will redirect to this URL after authorization
    return_url = url_for('auth.authorize', _external=True)

    current_app.logger.info('redirecting to EHR Authz. will return to: %s', return_url)

    current_app.logger.debug('passing iss as aud: %s', iss)
    return oauth.sof.authorize_redirect(
        redirect_uri=return_url,
        # SoF requires iss to be passed as aud querystring param
        aud=iss,
        # must pass launch param back when using EHR launch
        launch=launch,
    )


@auth_blueprint.route('/authorize')
def authorize():
    """
    Direct identity provider to redirect here after auth
    """
    # raise 400 if error passed (as querystring params)
    if 'error' in request.args:
        error_details = {
            'error': request.args['error'],
            'error_description': request.args['error_description'],
        }
        return error_details, 400
    # authlib persists OAuth client details via secure cookie
    #if not '_sof_authlib_state_' in session:
        #return f"session keys {session.keys()}", 400
        #return 'authlib state cookie missing; restart auth flow', 400

    # todo: define fetch_token function that requests JSON (Accept: application/json header)
    # https://github.com/lepture/authlib/blob/master/authlib/oauth2/client.py#L154
    token = oauth.sof.authorize_access_token(_format='json')
    iss = session['iss']
    current_app.logger.debug('iss from session: %s', iss)

    session['auth_info'] = {
        'token': token,
        'iss': iss,
        # debugging data
        'req': request.args,
        #'patient_data': response.json(),
    }

    frontend_url = current_app.config['LAUNCH_DEST']
    current_app.logger.info('redirecting to frontend app: %s', frontend_url)
    return redirect(frontend_url)


@auth_blueprint.route('/auth-info')
def auth_info():
    auth_info = session['auth_info']
    iss = session['auth_info']['iss']
    return {
        # debugging
        'token_data': auth_info['token'],

        "fakeTokenResponse": {
            "access_token": auth_info['token']['access_token'],
            "token_type": "Bearer",
        },
        "fhirServiceUrl": iss,
        "patientId":auth_info['token']['patient'],
    }


@auth_blueprint.route('/users/<int:user_id>')
def users(user_id):
    return {'ok':True}


@auth_blueprint.before_request
def before_request_func():
    current_app.logger.info('before_request session: %s', session)
    current_app.logger.info('before_request authlib state present: %s', '_sof_authlib_state_' in session)


@auth_blueprint.after_request
def after_request_func(response):
    current_app.logger.info('after_request session: %s', session)
    current_app.logger.info('after_request authlib state present: %s', '_sof_authlib_state_' in session)

    # todo: make configurable
    origin = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response
