import os
import sys
from os import path
import sqlite3
import argparse
from zipfile import ZipFile
from shutil import copyfile

class AdobeExtractor:
	def __init__(self, payload_dir, output_dir):
		self.payload_dir = payload_dir
		self.output_dir = output_dir
		self.work_dir = path.join(output_dir, 'temp_output')

		if not path.exists(self.work_dir):
			os.makedirs(self.work_dir)

	def extract(self):
		for compoment_name in os.listdir(self.payload_dir):
			compoment_dir = path.join(self.payload_dir, compoment_name)
			if path.isdir(compoment_dir):
				db_file = path.join(compoment_dir, 'install.db')
				work_dir = path.join(self.work_dir, compoment_name)
				if not path.exists(work_dir):
					os.makedirs(work_dir)
				if path.exists(db_file):
					self.proc_db(db_file, compoment_dir, work_dir, compoment_name)

	def proc_db(self, db_file, compoment_dir, work_dir, compoment_name):
		# Extract all zip files to `work_dir` first
		zip_list = [name for name in os.listdir(compoment_dir) \
					if name.endswith('.zip') and name.startswith('Assets')]

		# [ARK_ASSETS1]\filename
		for zip_path in zip_list:
			dir_name = '[ARK_ASSETS%s]' % zip_path[6]
			extract_dir = path.join(work_dir, dir_name)
			print('Extracting %s/%s ...' % (compoment_name, dir_name))
			with ZipFile(path.join(compoment_dir, zip_path), 'r') as zip_file:
				zip_file.extractall(extract_dir, zip_file.namelist())

		# Now read the database and copy files around.
		with sqlite3.connect(db_file) as conn:
			c = conn.cursor()
			c.execute('SELECT source, destination FROM InstallFile Order by SequenceNum')
			while True:
				entry = c.fetchone()
				if entry == None:
					break

				(src,dst) = entry

				src_path = path.join(work_dir, src)
				if not path.exists(src_path):
					print('%s does not exist!' % src, file=sys.stderr)
					continue

				print('Copy %s to %s...' % (src, dst))
				dst_path = path.join(self.output_dir, dst)
				dst_dir  = path.dirname(dst_path)
				if not path.exists(dst_dir):
					os.makedirs(dst_dir)

				copyfile(path.join(work_dir, src), dst_path)

			c.close()

		print('Extract complete.')

def main():
	parser = argparse.ArgumentParser(description='Adobe Payload extractor.')
	parser.add_argument('-p', '--payload-dir', type=str, dest='payload', nargs='?',
						help='Directory to the payload.', required=True)
	parser.add_argument('-o', '--output-dir', type=str, dest='output', nargs='?',
						help='Directory to put extracted files.', required=False)
	args = parser.parse_args()
	
	ae = AdobeExtractor(args.payload, args.output)
	ae.extract()

if __name__ == '__main__':
	main()