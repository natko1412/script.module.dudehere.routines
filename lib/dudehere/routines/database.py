import sys
import re
import xbmc
import xbmcaddon
import os
from dudehere.routines import *

IGNORE_UNIQUE_ERRORS = True
from vfs import VFSClass
class DatabaseClass:
	def __init__(self, quiet=False):
		self.quiet=quiet
		self._unique_str = 'column (.)+ is not unique$'

	def commit(self):
		if self.db_type == 'sqlite':
			print "Commiting to %s" % self.db_file
		else:
			print "Commiting to %s on %s" % (self.dbname, self.host)
		self.DBH.commit()

	def disconnect(self):
		if self.db_type == 'sqlite':
			print "Disconnecting from %s" % self.db_file
			self.DBC.close()
		else:
			print "Disconnecting from %s on %s" % (self.dbname, self.host)
			self.DBC.close()

	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def query(self, SQL, data=None,force_double_array=False):
		if data:
			self.DBC.execute(SQL, data)
		else:
			self.DBC.execute(SQL)
		rows = self.DBC.fetchall()
		if(len(rows)==1 and not force_double_array):
			return rows[0]
		else:
			return rows

	def query_assoc(self, SQL, data=None, force_double_array=False):
		self.DBH.row_factory = self.dict_factory
		cur = self.DBH.cursor()
		if data:
			cur.execute(SQL, data)
		else:
			cur.execute(SQL)
		rows = cur.fetchall()
		cur.close()
		if(len(rows)==1 and not force_double_array):
			return rows[0]
		else:
			return rows
	def execute(self, SQL, data=[]):
		try:
			if data:
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception, e:
			if IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):				
				print '****** SQL ERROR: %s' % e

	def execute_many(self, SQL, data):
		try:
			self.DBC.executemany(SQL, data)
		except Exception, e:
			if IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):				
				print '****** SQL ERROR: %s' % e	
				
class SQLiteDatabase(DatabaseClass):
	def __init__(self, db_file='', quiet=False, maindb=True):
		self.quiet=quiet
		self._unique_str = 'column (.)+ is not unique$'
		self.db_type = 'sqlite'
		self.lastrowid = None
		self.db_file = db_file		
		self._connect(maindb)

	def _connect(self, maindb):
		global ADDON
		if not self.quiet:
			print "Connecting to " + self.db_file
		try:
			from sqlite3 import dbapi2 as database
			if not self.quiet:
				print "%s loading sqlite3 as DB engine" % ADDON_NAME
		except:
			from pysqlite2 import dbapi2 as database
			if not self.quiet:
				print "%s loading pysqlite2 as DB engine"  % ADDON_NAME
		if not self.quiet:
			print "Connecting to SQLite on: " + self.db_file
		self.DBH = database.connect(self.db_file)
		self.DBC = self.DBH.cursor()
		
		if maindb and ADDON.get_setting('database_sqlite_init') != 'true':
			self._initialize()
	

		
class MySQLDatabase(DatabaseClass):
	def __init__(self, host, dbname, username, password, port, quiet=False):
		self.quiet=quiet
		self._unique_str = '1062: Duplicate entry'
		self.db_type = 'mysql'
		self.lastrowid = None
		self.host = host
		self.dbname = dbname
		self.username=username
		self.password = password
		self.port = port
		self._connect()

	def _connect(self):
		global ADDON
		try:	
			import mysql.connector as database
			if not self.quiet:
				print "%s loading mysql.connector as DB engine" % ADDON_NAME
			dsn = {
					"database": self.dbname,
					"host": self.host,
					"port": int(self.port),
					"user": str(self.username),
					"password": str(self.password),
					"buffered": True
			}
			self.DBH = database.connect(**dsn)
		except Exception, e:
			print '****** %s SQL ERROR: %s' % (ADDON_NAME, e)
		self.DBC = self.DBH.cursor()
		if ADDON.get_setting('database_mysql_init') != 'true':
			self._initialize()
	
	def execute(self, SQL, data=[]):					
		try:
			if data:
				SQL = SQL.replace('?', '%s')
				self.DBC.execute(SQL, data)
			else:
				self.DBC.execute(SQL)
			try:
				self.lastrowid = self.DBC.lastrowid
			except:
				self.lastrowid = None
		except Exception, e:
			if IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):				
				print '******SQL ERROR: %s' % e

	def execute_many(self, SQL, data):
		try:
			SQL = SQL.replace('?', '%s')
			self.DBC.executemany(SQL, data)
		except Exception, e:
			if IGNORE_UNIQUE_ERRORS and re.match(self._unique_str, str(e)):				
				print '****** SQL ERROR: %s' % e

	def query(self, SQL, data=None, force_double_array=False):
		if data:
			SQL = SQL.replace('?', '%s')
			self.DBC.execute(SQL, data)
		else:
			self.DBC.execute(SQL)
		rows = self.DBC.fetchall()
		if(len(rows)==1 and not force_double_array):
			return rows[0]
		else:
			return rows