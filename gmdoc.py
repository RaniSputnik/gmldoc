import sys, os, shutil, xml, re
import xml.etree.ElementTree as ET
from jinja2 import Environment, PackageLoader
JINJA_ENV = Environment(loader=PackageLoader('gmdoc', 'templates'))

# Templates
METHOD_TEMPLATE = JINJA_ENV.get_template('layout.html')

# Basic types
TYPE_REAL = 'real'
TYPE_STRING = 'string'

class Extension():
	def __init__(self, name, description):
		self.name = name
		self.description = description

# Represents a method in the source code
class Method():
    def __init__(self, name, syntax):
    	self.name = name
        self.params = []
        self.syntax = syntax
        self.description = ''

# Represents a method parameter in the source code
class Param():
	def __init__(self, name, type, desc):
		self.name = name
		self.type = type
		self.description = desc

# Kills the program and prints the given message
def die(message):
	print(message)
	sys.exit()

# Print the intended usage of the program
def usage():
	die("usage: "+sys.argv[0]+" <target.project.gmx>")

# Reads an xml file and returns the root node
def read_xml(the_dir):
	the_file = open(the_dir,"r")
	contents = the_file.read()
	the_file.close()
	return ET.fromstring(contents)

# Extracts all comments from the given code
def extract_comment_text(code):
	state = 0
	last = ''
	result = ''
	for char in code:
		# Once we have read the entire first comment
		# section and we hit code, we are done. Return
		# the result
		if state == -1:
			if char == '/' or char == '*':
				state = 0
			elif char != ' ':
				return result

		if state == 0:
			if char == '\n':
				state = -1
			elif last == '/':
				if char == '*':
					result += last + char
					state = 2
				elif char == '/':
					result += last + char
					state = 1
		elif state == 1:
			if char == '\n':
				state = 0
			result += char
		elif state == 2:
			if last == '*' and char == '/':
				state = 0
			result += char
		last = char
	return result

# Removes any / * and spaces from the start of the given string
def strip_leading_comment_markup(code):
	i = 0
	for char in code:
		if char != ' ' and char != '/' and char != '*':
			return code[i:]
		else:
			i += 1
	return ''

# 
def strip_token(token, code):
	i = code.find(token)
	if i >= 0:
		return code[i+len(token):].strip()


# Documents the given project file
def doc(project_file, outdir):
	# TODO normalize outdir - remove trailing /
	# and remove any leading dots and / 

	# TODO create a proper extension
	extension = Extension('TODO Title','TODO Description')

	# Read the contents of the project file
	print("Reading project file...");
	project_dir = os.path.dirname(project_file)
	project_xml = read_xml(project_file)
	print(">> Successfully read project file");
	# Initialize all the project things
	project_methods = []
	# Read all the project scripts and extract
	# doc information from them
	print("Reading scripts...")
	for script in project_xml.iter("script"):
		script_path = script.text.replace("\\","/")
		script_path = os.path.join(project_dir,script_path)
		script_name_and_ext = os.path.basename(script_path)
		script_name = os.path.splitext(script_name_and_ext)[0]
		# Skip scripts that start with an underscore
		if script_name[0] == '_': 
			print('Skipping private script ' + script_name)
			continue
		else:
			print("Reading script " + script_name + "...")
		# Read the script file
		script_file = open(script_path,"r")
		code = script_file.read()
		script_file.close()
		comments = extract_comment_text(code).split('\n')
		syntax = strip_leading_comment_markup(comments[0])
		comments = comments[1:]
		# Generate a method object from the script file
		method = Method(script_name, syntax)
		desc = ''
		for comment in comments:
			the_param = strip_token("@param", comment)
			the_return = strip_token("@return", comment)
			if the_param:
				the_param = the_param.split(' ',1)
				method.params.append(Param(the_param[0], TYPE_REAL, the_param[1]))
			elif the_return:
				method.return_value = the_return
			else:
				desc += strip_leading_comment_markup(comment)
		method.description = desc
		print(method.description)
		project_methods.append(method)
	print(">> Successfully read scripts")

	# Write the HTML files
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	for method in project_methods:
		print("Rendering file %s", method.name)
		render_params = {
			'extension': extension,
			'method': method,
			'all_methods': project_methods,
			'path': outdir,
			# Uncomment these lines when testing locally
			# 'stylesheet_url': '../styles/all.css',
		}
		the_html = METHOD_TEMPLATE.render(render_params)
		text_file = open(os.path.join(outdir,method.name + '.html'), "w")
		text_file.write(the_html)
		text_file.close()

# Check command line args
if len(sys.argv) < 2:
	print("Must supply a project file")
	usage()

# Set and validate the target project file
TARGET_FILE = sys.argv[1]
print("Project target: "+TARGET_FILE)
if not os.path.isfile(TARGET_FILE):
	die("Project file doesn't exist!")

# Start documenting the given file
doc(TARGET_FILE, 'output')
