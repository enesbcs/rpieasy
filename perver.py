#!/usr/bin/python
# coding: utf-8
# Perver - tiny Python 3 server for perverts.
# Copyright (C) 2016 SweetPalma <sweet.palma@yandex.ru>
# All rights reserved.
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

from sys import platform as os_platform
from hashlib import sha1 as hash_id
from urllib.parse import unquote
from mimetypes import guess_type
from traceback import format_exc
from functools import wraps
import threading as thread
import concurrent.futures
import logging as log
import asyncio
import base64
import time
import sys
import os
import re


# Version control:
__author__ = 'SweetPalma'
__version__ = '0.30'


# Custom internal exceptions:
class PerverException(Exception):
	def __init__(self, message):
		self.message = str(message)


# Handling HTTP requests:
class PerverHandler:

	# Path substitution pattern:
	path_pattern = re.compile(r'(\{.+?\})')
	
	# Making server link:
	def __init__(self, server):
		self.server = server
	
	# Handling requests:
	async def handle_request(self, reader, writer):
		
		# Preparing basic values:
		peername = writer.get_extra_info('peername')
		ip, port = peername[0], peername[1]
		
		# Client basic values:
		self.ip = ip
		self.port = port
		self.reader = reader
		self.writer = writer
		self.time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
		
		# Client info, used in logging:
		client_info = ' '.join([
			self.time,
			self.ip,
		])
		
		# Terminator shortcut:
		killer = PerverException
		request_max = 65535
		# Handling:
		try:
		
			# Reading header until EOF:
			header, length = b'', 0
			while True:
				try:
				
					# Reading:
					line = await reader.readline()
					
					# Setting request type and maximal request size at start:
					if len(header) == 0:
						if line.startswith(b'POST'):
							request_type = b'POST'
							request_max = self.server.post_max
						else:
							request_type = b'GET'
							request_max = self.server.get_max
					
					# Setting break:
					if line == b'\r\n' or not line:
						break
						
					# Reading content length:
					if line.startswith(b'Content-Length'):
						length = int(line.split(b':')[1])
						
					# Reading header:
					header = header + line
				
				# Some spooky errors during reading:
				except:
					break
			
			# Reading content:
			content = b''
			if 0 < length < request_max:
				content = await reader.readexactly(length)
				
			# Close connection in case of big file:
			elif length > request_max:
				self.writer.close()
				raise killer('REQUEST IS TOO BIG')
			
			# Parsing data:
			self.client = await self.build_client(header, content)
			client = self.client
			
			# In case of disconnection:
			if not client:
				self.writer.close()
				raise killer('CLIENT CLOSED CONNECTION')
				
			# Logging full information:
			client_info = client_info + ' ' + ' '.join([
				client.type,
				client.path,
			])
	
			# Checking routing:
			route_post = self.check_route(client.path, self.server.route_post)
			route_get = self.check_route(client.path, self.server.route_get)
			if client.type == 'POST' and route_post:
				raise killer((await self.respond_script(*route_post)))
			if client.type == 'GET' and route_get:
				raise killer((await self.respond_script(*route_get)))
				
			# Checking static files:
			for dir, real in self.server.route_static.items():
				if client.path.startswith(dir):
					filepath = client.path.replace(dir, real, 1)
					raise killer((await self.respond_file(filepath[1:])))
			
			# Routing 404 error:
			raise killer((await self.respond_error(404)))
			
		# Timeout/Cancelled:
		except concurrent.futures._base.CancelledError:
			await self.respond_error(500)
			log.info(client_info + ' TIMED OUT')
			
		# Terminator:
		except killer as exception:
			log.info(client_info + ' ' + exception.message)
			
	# Sending file:
	async def respond_file(self, path):
		try:
			with open(path, "rb") as file:
				size = os.path.getsize(path)
				return (await self.respond(
					status = 200, 
					content = file.read(), 
					type = self.get_mime(path), 
					length = size
				))
		# No file found:
		except IOError:
			return (await self.respond_error(404))
				
	# Sending error message:
	async def respond_error(self, number, custom=None):
		error = {
			400: 'Bad Request',
			404: 'Not Found',
			500: 'Internal Error',
		}
		error_text = number in error and error[number] or 'Unknown Error'
		error_cont = str(number) + ' ' + error_text
		return (await self.respond(number, error_cont))
		
	# Executing client script and sending it response:
	async def respond_script(self, script, keys={}):
		script_result = (await script(self.client, **keys)) or b''
		return (await self.respond(
			status = self.client.status, 
			content = script_result,
			header = self.client.header, 
			type = self.client.mime
		))
	
	# Pure data response:
	async def respond(self, status, content=b'', type='text/html', length=None, header={}):
		
		# Forming header:
		encoding = self.server.encoding
		self.header = 'HTTP/1.1 ' + str(status) + '\r\n'
		self.form_header('Accept-Charset', encoding)
		self.form_header('Server', 'Perver/' + __version__)
		self.form_header('Access-Control-Allow-Origin', '*')
		
		# Setting mime type (and encoding for text):
		if type.startswith('text/'):
			ctype = type + ';charset=' + encoding
		else:
			ctype = type
		self.form_header('Content-Type', ctype)
		
		# Working with custom headers:
		for key, value in header.items():
			self.form_header(key, value)
			
		# Encoding unicode content:
		if not isinstance(content, bytes):
			content = content.encode(encoding)
			
		# Forming content length:
		length = length or len(content)
		self.form_header('Content-Length', str(length))
		
		# Forming response:
		header = self.header.encode(encoding)
		response = header + b'\r\n' + content + b'\r\n'
		
		# Go:
		self.writer.write(response)
		try:
		 self.writer.write_eof()
		except:
		 pass
		# Done:
		return status
	
	# Making client ID using cut SHA hash on client IP and User-Agent:
	def get_id(self, clnt):
		ident = str(clnt.ip) + str(clnt.agent)
		ident_encoded = ident.encode(self.server.encoding)
		hashed = hash_id(ident_encoded).digest()[:self.server.length_id]
		cooked = base64.urlsafe_b64encode(hashed).decode(self.server.encoding)
		return cooked[:-2] # Removed two last minuses for better readibility.

	# Power of regexp!
	def check_route(self, path, map):
		
		# Pure path:
		if path in map:
			return (map[path], {})
			
		# Path with substitutions:
		right_path, groups = None, sys.maxsize
		for route in map:
		
			# Removing retarded slash in the end of path:
			path = path.endswith('/') and path[:-1] or path
		
			# Patterns:
			path_pattern = '^' + self.path_pattern.sub('([^/]+)', route) + '$'
			matched = re.match(path_pattern, path)
			
			# Testing route:
			if matched:
				keys = [key[1:-1] for key in self.path_pattern.findall(route)]
				values = list(matched.groups())
				if len(values) < groups:
					groups = len(values)
					right_path = (map[route], dict(zip(keys, values)))

		# In case of fail:
		return right_path

	# Appending certain header lines:
	def form_header(self, arg, var):
		self.header = self.header + arg + ': ' + var + '\r\n'
		
	# Retrieving type:
	def get_mime(self, path):
		fname, extension = os.path.splitext(path)
		if extension == '':
			return guess_type(path)[0] or 'text/html'
		else:
			return guess_type(path)[0] or 'application'
	
	# Parsing GET and COOKIES:
	async def parse(self, path):
		# Preparing %key%=%value% regex:
		try:
		 get_word = '[^=;&?]'
		 get_word2 = '[^;&?]'
		 pattern = '(%s+)=(%s+)' % (get_word, get_word2)

		 # Unquoting map:
		 unq = lambda x: map(unquote, x)
		
		 # Replacing retarded pluses to spaces in path:
		 path = path.replace('+', ' ')
		
		 # Working:
		 matched = [unq(x) for x in re.findall(pattern, path)]
		except Exception as e:
		 print(e)
		return dict(matched)
			
	# Parsing POST multipart:
	async def parse_post(self, content, types, boundary):
	
		# Establishing default encoding:
		encoding = self.server.encoding
		types = str(types).strip()
		# Parsing multipart:
		if types == 'multipart/form-data':
			# Splitting request to fields:
			fields = content.split(boundary)
			fields_dict = {}

			# Turning `em to dictionary:
			for field in fields:
			
				# Checking:
				field_rows = field.split(b'\r\n\r\n')
				if len(field_rows) >= 2:
					try:
						header = field_rows[0]
						value = field_rows[1]
						if len(field_rows)>2:
						 for x in range(2,len(field_rows)):
						  value += b'\r\n\r\n' + field_rows[x]
						value = value[:-4]
						# Decoding key:
						key = re.findall(b';[ ]*name="([^;]+)"', header)[0]
						key = key.decode(encoding)
						# Checking content-type:
						ctype = re.search(b'Content-Type: ([^;]+)$', header)
						# File upload field:
						if ctype:
							if value == b'' or value == b'\r\n':
								continue
							ctype = ctype.group()
							fname = re.findall(b';[ ]*filename="([^;]+)"', header)
							fname = len(fname) == 1 and fname[0] or b'unknown'
							fields_dict[key] = {
								'filename': fname.decode(encoding),
								'mime': ctype.decode(encoding),
								'file': value,
							}
						# Text field:
						else:
							fields_dict[key] = value.decode(encoding)
					except Exception as e:
						print("Perver exception ",e)
			return fields_dict
		
		# Parsing average urlencoded:
		else:
			if isinstance(content, bytes):
				content = content.decode(encoding)
			return await self.parse(content)
		
	# Parsing client data:
	async def build_client(self, header_raw, content_raw=b''):
	
		# Safe dict values:
		def safe_dict(dictionary, value, default):
			if value in dictionary:
				return dictionary[value]
			else:
				return default
				
		# Decoding:
		try:
		
			# Decoding header:
			header_decoded = header_raw.decode(self.server.encoding)
#			print(header_decoded)#debug
			# Three basic values: request type, path and version:
			pattern = r'^(GET|POST) ([A-Za-z0-9_+=.~?&*%/\-,]+) (HTTP/1.1|HTTP/1.0)' # watch for special characters?
			unpacked = re.findall(pattern, header_decoded)
			if len(unpacked) > 0:
				type, path, version = re.findall(pattern, header_decoded)[0]
			else:
#				raise PerverException('WRONG CLIENT HEAD')
#				print('WRONG CLIENT HEAD')
#				print(header_raw)
				return False
			# Splitting GET and PATH:
			if '?' in path:
				path, GET = path.split('?')
#				GET = GET.replace("+"," ")
#				print(GET)
			else:
				GET = ''
		
			# Raw header to header dictionary:
			pattern = '([^:]+):[ ]*(.+)\r\n'
			header = dict(re.findall(pattern, header_decoded))
			
			# Basic client variables:
			client = PerverClient()
			client.version = version
			client.type, client.path = type, unquote(path)
			client.path_dir = '/'.join(unquote(path).split('/')[:-1])
			# Client header:
			client.header_raw, client.content_raw = header_raw, content_raw
			client.content_type = safe_dict(header, 'Content-Type', '')
			client.content_length = safe_dict(header, 'Content-Length', 0)
			client.agent = safe_dict(header, 'User-Agent', 'Unknown')
			client.mime = self.get_mime(client.path)
			client.form_type = client.content_type.split(';')[0]
			# Server client values:
			client.ip, client.port, client.time = self.ip, self.port, self.time
			client.id = self.get_id(client)
			
			# POST boundary:
			boundary = re.findall('boundary=(-*[0-9,a-z,A-Z]*)', client.content_type)
			if len(boundary) > 0:
				boundary = boundary[0].encode(self.server.encoding)
			else:
				boundary = b''
			
			# POST/GET/COOKIES:
			client.get =     await self.parse(GET)
			client.post =    await self.parse_post(content_raw, client.form_type, boundary)
			client.cookie =  await self.parse(safe_dict(header, 'Cookie', ''))
			
			# Client ID cookie, can be overrided later:
			client.header['Set-Cookie'] = 'id=' + client.id
			
			# Client server-side container:
			if not client.id in self.server.client:
				self.server.client[client.id] = {}
			client.container = self.server.client[client.id]
			
			# Fixing client path dir:
			if client.path_dir == '':
				client.path_dir = '/'
			
			# Done!
			return client
			
		# In case of fail:
		except BaseException as exc:
			log.warning('Error parsing user request.')
			await self.respond_error(400) 
			raise exc
			
# Script client:
class PerverClient:
	
	# GET/POST arguments:
	get  = {}
	post = {}
	
	# Client headers:
	status = 200
	header = {}
	cookie = {}
	mime = 'text/html'
	
	# Redirection:
	def redirect(self, page):
		""" Redirects client to a certain page using 302 status code. """
		self.header['Location'] = page
		self.status = 302
		return 'Redirecting...'
	
	# Templating:
	def template(self, text, **replace):
		""" Used in templating - works same as str.format. """
		return text.format(**replace)
		
	# Rendering page:
	def render(self, filename, **replace):
		""" Same as template, but used in files. Returns templated file. """
		file = open(filename, 'r')
		return self.template(file.read(), **replace)
	
	# Retrieving file:
	def file(self, filename):
		""" Simply returns file contents, binary. """
		self.mime = guess_type(filename)[0]
		file = open(filename, 'rb')
		return file.read()
	
	# Own header:
	def set_header(self, key, value):
		""" Sets custom client HTTP header. """
		self.header[key] = value
	
	# Cookies:
	def set_cookie(self, name, value):
		""" Sets custom client cookie, overriding default Perver ID Cookie. """
		self.header['Set-Cookie'] = name + '=' + value +';'
		
	# Status:
	def set_status(self, status):
		""" Sets custom response status, overriding default 200. """
		self.status = status
		
	# Mime:
	def set_mime(self, mime):
		""" Sets custom mime response. """
		self.mime = mime
		
	# Making HTML template:
	def html(self, body, head='', doctype='html'):
		""" HTML-correct template for nice pages. """
		doctype = '<!DOCTYPE %s>' % doctype
		head = '\r\n'.join(['<head>', head, '</head>'])
		body = '\r\n'.join(['<body>', body, '</body>'])
		return '\r\n'.join([doctype, head, body])
		
	# Making forms:
	def form(self, action, method, *inputs, id='', multipart=False):
		""" Used for building forms. """
		if multipart:
			enctype='multipart/form-data'
		else:
			enctype='application/x-www-form-urlencoded'
		form_desc = (action, method, id, enctype)
		html = '<form action="%s" method="%s" id="%s" enctype="%s">' % form_desc
		inputs = [list(inp.items()) for inp in inputs]
		for input in inputs:
			args = ' '.join('%s="%s"' % arg for arg in input)
			html = '\r\n'.join([html, '<input %s><br>' % args])
		return ''.join([html, '</form>'])
		
	# Multipart form:
	def form_multipart(self, *args, **kargs):
		""" Works same as previous, but with multipart argument set to True."""
		kargs['multipart'] = True
		return self.form(*args, **kargs)
		
	# Part of the previous function:
	def input(self, name, **kargs):
		""" Single form input. """
		return dict(name=name, **kargs)
	
	# Input submit:
	def input_submit(self, value='Submit', **kargs):
		""" Form submit button. """
		return dict(type='submit', value=value, **kargs)

		
# Perver Server itself:
class Perver:

	# PARAMETERS:
	# Main server values:
	encoding = 'utf-8'
	backlog  = 5
	timeout  = 30
	
	# Maximal requests length:
	get_max  = 1024 * 8
	post_max = 1024 * 1024 * 100
	
	# Client ID length:
	length_id = 10
	# I highly recommend not to change this value.
	
	# Routing paths:
	route_get  = {}
	route_post = {}
	route_static = {}
	
	# Active clients list:
	client = {}
	
	# METHODS:
	# Routing GET:
	# DECORATOR:
	def get(self, path):
		""" Binds all GET requests from path to certain function. """
		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwds):
				return func(*args, **kwds)
			self.route_get[path] = wrapper
			return wrapper
		return decorator
	
	# Routing POST:
	# DECORATOR:
	def post(self, path):
		""" Binds all POST requests from path to certain function.  """
		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwds):
				return func(*args, **kwds)
			self.route_post[path] = wrapper
			return wrapper
		return decorator
	
	# Global routing:
	# DECORATOR:
	def route(self, path):
		""" Binds all POST/GET requests from path to certain function. """
		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwds):
				return func(*args, **kwds)
			self.route_post[path] = wrapper
			self.route_get[path] = wrapper
			return wrapper
		return decorator
		
	# Adding static route:
	def static(self, web, local):
		""" Uses local path for serving static files for web requests. """
		local = local.replace('\\', '/')
		if not (local.startswith('/') and os.path.isabs(local)):
			local = '/' + local
		if not local.endswith('/'):
			local = local + '/'
		self.route_static[web] = local
	
	# Starting:
	def start(self, host='', port=80):
		""" Starts the (mostly) infinite loop of server. """
		# Configuring output:
		self.host, self.port = host, port
		log.basicConfig(level=log.ERROR, format='%(levelname)s: %(message)s')
		#log.basicConfig(level=log.INFO, format='%(levelname)s: %(message)s')
		
		# Nice header for Windows:
		if os_platform == 'win32':
			os.system('title Perver v' + __version__)
		
		# Trying running:
		try:
			self._loop = asyncio.get_event_loop() 
			self._server = asyncio.start_server(
				self.handler, 
				host=host, 
				port=port, 
				backlog=self.backlog,
				reuse_address=True,
			)
			self._server = self._loop.run_until_complete(self._server)
			start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
			log.info('Perver has started at ' + start_time + '.')
			self._loop.run_forever()
			
		# In case of Skype on 80 port, access denials and other socket errors:
		except OSError:
			log.error('OS error, probably server is already running at that port \
			           or user is not sudoer.')
	
	# Stop?
	def stop(self):
		""" Stops the Perver. """
		self._server.close()
		self._loop.stop()
			
	# HTTP request handler:
	async def handler(self, reader, writer):
		try:
			handler = PerverHandler(self)
			await asyncio.wait_for(
				handler.handle_request(reader, writer), 
				timeout=self.timeout
			)
		except KeyboardInterrupt:
			log.warning('Interrupted by user.')
			self.stop()
		except SystemExit:
			self.stop()
		except asyncio.TimeoutError:
			pass
		except:
			log.warning('Exception caught! \r\n' + format_exc())
			
			
# Pythonic async database
class PerverDB:
	
	# Initialization:
	def __init__(self, filename):
		pass
			
	
# Not standalone:
if __name__ == '__main__':
	print('Perver is not a standalone application. Use it as framework.')
	print('Check "github.com/SweetPalma/Perver" for details.')
