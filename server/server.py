import logging

from .user import User

log = logging.getLogger(__name__)

async def server(websocket, path):
	log.info('New connection from \'%s:%i\'' % (tuple(websocket.remote_address)[:2]))
	
	new_user = await User.register(websocket)
	if not new_user:
		return

	await new_user.send(1, 'HELLO', new_user.as_safe_dict())

	try:
		await new_user.loop()
	finally:
		await new_user.unregister()