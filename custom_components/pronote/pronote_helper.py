"""Client wrapper for the Pronote integration."""

import pronotepy
import json
import logging

_LOGGER = logging.getLogger(__name__)

def get_pronote_client(data, config_dir: str) -> pronotepy.Client | pronotepy.ParentClient | None:
    _LOGGER.debug(f"Coordinator uses connection: {data['connection_type']}")

    if data['connection_type'] == 'qrcode':
        return get_client_from_qr_code(data, config_dir)
    else:
        return get_client_from_username_password(data)

def get_client_from_username_password(data) -> pronotepy.Client | pronotepy.ParentClient | None:
    url = data['url'] + ('parent' if data['account_type'] == 'parent' else 'eleve') + '.html'

    ent = None
    if 'ent' in data:
        ent = getattr(pronotepy.ent, data['ent'])

    if not ent:
        url += '?login=true'

    try:
        client = (pronotepy.ParentClient if data['account_type'] == 'parent' else pronotepy.Client)(
            url,
            data['username'],
            data['password'],
            ent
        )
        _LOGGER.info(client.info.name)
    except Exception as err:
        _LOGGER.critical(err)
        return None

    return client

def get_credentials_file_path(username, config_dir) -> str:
    return f"{config_dir}/pronote_qr_credentials_{username}.txt"

def get_client_from_qr_code(data, config_dir: str) -> pronotepy.Client | pronotepy.ParentClient | None:

    if 'qr_code_json' in data: # first login from QR Code JSON

        # login with qrcode json
        qr_code_json = json.loads(data['qr_code_json'])
        qr_code_pin = data['qr_code_pin']
        uuid = data['qr_code_uuid']

        # get the initial client using qr_code
        client = (pronotepy.ParentClient if data['account_type'] == 'parent' else pronotepy.Client).qrcode_login(
            qr_code_json,
            qr_code_pin,
            uuid
        )

        qr_code_url = client.pronote_url
        qr_code_username = client.username
        qr_code_password = client.password
        qr_code_uuid = client.uuid
    else:
        qr_code_url = data['qr_code_url']
        qr_code_username = data['qr_code_username']
        qr_code_password = None
        qr_code_uuid = data['qr_code_uuid']

    credentials_file_path = get_credentials_file_path(qr_code_username, config_dir)

    if qr_code_password is None:
        qr_code_password = open(credentials_file_path, "r").read()

    _LOGGER.info(f"Coordinator uses qr_code_username: {qr_code_username}")
    _LOGGER.info(f"Coordinator uses qr_code_pwd: {qr_code_password}")

    client = (pronotepy.ParentClient if data['account_type'] == 'parent' else pronotepy.Client).token_login(
        qr_code_url,
        qr_code_username,
        qr_code_password,
        qr_code_uuid
    )

    qrcredentials = open(credentials_file_path, "w+")
    qrcredentials.writelines([client.password]) # always store the latest generated password
    qrcredentials.close()

    return client

