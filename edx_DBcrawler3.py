from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,StaleElementReferenceException,ElementNotVisibleException,WebDriverException,TimeoutException,ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from six.moves import html_parser
from tqdm import tqdm
from pathlib import Path
import pandas as pd
import traceback
import errno
import time
import webbrowser
import html
import string
import re
import json
import os
import getpass
import sys
import csv


chrome_options = Options()  
chrome_options.add_argument('headless')
chrome_options.add_argument('window-size=1920x1080')
chrome_options.add_argument("--log-level=3")  # fatal 
chrome_options.add_argument('--disable-gpu')


driver_loc = './chromedriver'

COURSETABLE_EXCEL = 'course table.xlsx'
FOLDERDIR = 'HTMLs'
DB_ALLDB = 'all_dis2.json'
EDXACCOUNT = 'account info.json'

def mkdir_p(path, mode=0o777):
	"""
	Create subdirectory hierarchy given in the paths argument.
	"""
	try:
		os.makedirs(path, mode)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def clean_filename(s, minimal_change=False):
	"""
	Sanitize a string to be used as a filename.
	If minimal_change is set to true, then we only strip the bare minimum of
	characters that are problematic for filesystems (namely, ':', '/' and
	'\x00', '\n').
	"""

	# First, deal with URL encoded strings
	h = html_parser.HTMLParser()
	s = html.unescape(s)

	# strip paren portions which contain trailing time length (...)
	s = (
		s.replace(':', '-')
		.replace('/', '-')
		.replace('\x00', '-')
		.replace('\n', '')
	)

	if minimal_change:
		return s

	s = s.replace('(', '').replace(')', '')
	s = s.rstrip('.')  # Remove excess of trailing dots

	s = s.strip().replace(' ', '_')
	valid_chars = '-_.()%s%s' % (string.ascii_letters, string.digits)
	return ''.join(c for c in s if c in valid_chars)


def course_selection(course_list):

	chosen_no = int(input('enter number of courses (type 9999 for crawling every course)'))
	chosen_idx =[]
	if chosen_no == 9999:
		return course_list

	print ('list of courses in dashboard')

	df = pd.DataFrame(course_list).sort_values('name')

	for course,idx in zip(df.name,df.index):
		print (str(idx).ljust(5) +' : ' + course)
	array_c = [i for i in range(0,len(course_list)) ]

	while True:
		if chosen_no == 0:
			break

		chosen_course_id = int(input('enter course number '))
		if chosen_course_id in array_c:
			chosen_idx.append(chosen_course_id)
			print (df.name[chosen_course_id] , ' : ', df.url[chosen_course_id])
			chosen_no-=1
		else:
			print ('wrong course id. Try again!!!!!!!!')
	return df.loc[chosen_idx]

def selected_course_from_excel(course_list):
	df = pd.DataFrame(course_list)
	df_coursetable = pd.read_excel(COURSETABLE_EXCEL)
	chosen_idx = list()
	for url in df_coursetable['course url']:
		index_obj = df[df['url']==url].index
		print (df.name[index_obj[0]] , ' : ', df.url[index_obj[0]])
		chosen_idx.append(index_obj[0])
	return(df.loc[chosen_idx],df_coursetable['directory'])

def find_role(string):
	set_role = ['Community TA','Staff']
	for role in set_role:
		if re.search(role,string):
			return(role)
	return('n/a')


def savetextfile(filename,content): 
	with open(filename,'a',encoding='utf-8') as f:
		f.write(content)

		
def readtextfile(filename): 
	with open(filename,'r',encoding='utf-8') as f:
		all_response = f.read()
	os.remove(filename)
	return('{{\n {} \n}}'.format(all_response[1:-1]))

def write_log(filename,data):
	with open(filename,"a+",newline='',encoding='utf-8') as f:
		write_obj = csv.writer(f)
		write_obj.writerow(data)

def selected_course_2_csv(selected_course):
	filename = time.strftime("%Y%m%d-%H%M%S")+ "_selected_file.csv"
	write_log(filename,["Course title","URL"])
	for tmp_name,tmp_url in zip(selected_course.name,selected_course.url):
		write_log(filename,[ tmp_name, tmp_url ])

		


class DB_crawler():
	
	def __init__(self):
		
		#self.usr = input('username(email): ')
		#self.pwd = getpass.getpass(prompt='password: ',stream=sys.stderr)
		with open(EDXACCOUNT,'r') as f:
			json_f = json.loads(f.read())
		self.usr = json_f['edXaccount']
		self.pwd = json_f['edXpassword']
		self.driver = webdriver.Chrome(executable_path=driver_loc,options=chrome_options)

	
	def log_in(self):
		sign_in_url="https://courses.edx.org/login?next=/dashboard"
		self.driver.get(sign_in_url)
		time.sleep(2)
		self.driver.find_element_by_id("login-email").send_keys(self.usr)
		self.driver.find_element_by_id("login-password").send_keys(self.pwd)
		#self.driver.find_element_by_id("login-remember").click()
		self.driver.find_element_by_class_name("login-button").click()
	

	def load_all_thread(self):

		time.sleep(2)

		while(1):
			time.sleep(2)
			try:
				loadmore = self.driver.find_element_by_class_name('forum-nav-load-more').click()
			except StaleElementReferenceException:
				continue
			except (NoSuchElementException):
				#w_flag-=1
				#if w_flag <0:
				break
		return self.driver.find_elements_by_class_name("forum-nav-thread")

	
	def load_thread(self):
		try:
			self.driver.find_element_by_class_name('forum-nav-load-more').click()
			WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'forum-nav-load-more')))
			time.sleep(2)
		except (NoSuchElementException,TimeoutException):
			return(0)
		
		return(1)
	
	def load_comment(self,cur_obj):
		
		load_comment_btns = cur_obj.find_elements_by_xpath('//*[@class="btn-link action-show-comments"]')
		for btn in load_comment_btns:
			try:
				btn.click()
			except (ElementNotVisibleException,ElementNotInteractableException):
				continue

			
	def load_response_more(self):
		try:
			self.driver.find_element_by_class_name('load-response-button').click()

			WebDriverWait(self.driver, 5
				).until(EC.presence_of_element_located((By.CLASS_NAME, 'loading-animation')))

			WebDriverWait(self.driver, 180
				).until_not(EC.presence_of_element_located((By.CLASS_NAME, 'loading-animation')))


		except (TimeoutException,NoSuchElementException):
			return(0)

		return(1)


	def load_init_response(self):
		try:
			WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'loading-animation')))
			WebDriverWait(self.driver, 30).until_not(EC.presence_of_element_located((By.CLASS_NAME, 'loading-animation')))

		except (TimeoutException,NoSuchElementException):
			pass

	def handling_click_cat(self,webdriver_obj):
		while(1):
			try:
				webdriver_obj.click()
				break
			except WebDriverException:
				time.sleep(2)
			except Exception as e:
				print(e)
	
	def list_dash_course(self):
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "course-container")))
		print('successfully logged in')
		time.sleep(2)
		courses = self.driver.find_elements_by_class_name("course-container") 
		course_list = []
		print('extracted ',len(courses) ,  ' courses name and link in dashboard')
		for course in courses:
			c_name =course.find_element_by_class_name('course-title').text
			c_url = course.find_element_by_css_selector('a').get_attribute('href')
			course_list.append({'name':c_name, 'url':c_url}) 
		return(course_list)

	
	def access_discussion(self,course_name, url): 
		self.current_thread = 0
		self.coursename = course_name
		self.courseurl = url
		self.driver.get(self.courseurl)
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "navbar-nav")))
		self.driver.find_element_by_xpath('//*[@class="nav-item " or @class="nav-item active"]//*[contains(text(), "Discussion")]').click()

		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "discussion-body")))
		while(True):
			self.discuss_cat_list = self.driver.find_elements_by_xpath('//*[@class="forum-nav-browse-menu-item"]//*[@class="forum-nav-browse-title"]')
			self.cat_name_list = [cat.text.split(',\n') for cat in self.discuss_cat_list]

			if [''] not in self.cat_name_list:
				break

		print('number of categories before filter: ',len(self.discuss_cat_list))
		outer_layer_cat = [i[0] for i in self.cat_name_list if len(i) > 1]
		#filter_out_list = []
		for idx,cat_name in enumerate(self.cat_name_list):
			if len(cat_name) == 1 and cat_name[0] in outer_layer_cat:
				#filter_out_list.append(cat_name_list[idx])
				del self.discuss_cat_list[idx]
				del self.cat_name_list[idx]

		print('number of categories after filter: ', len(self.cat_name_list))
		print('list of crawled categories')
		print(*self.cat_name_list,sep='\n')
		time.sleep(3)
		for cat_idx,(cat,cat_name) in enumerate(zip(self.discuss_cat_list,self.cat_name_list)):
			self.access_cat(cat_idx,cat,cat_name)
		print('{} total threads were successfully crawled'.format(self.current_thread+1))

		if not os.path.exists('tmp_dis'):
			savetextfile('tmp_dis','')
		
		return(json.loads(readtextfile('tmp_dis')))
		
	def access_cat(self,cat_idx,cat,cat_name):
		#WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH,'//span[contains(text(),"{}")]'.format(cat.text.split(',\n')[0])))).click()
		cat.click()
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,'//div[@class="forum-nav-browse-menu-wrapper" and @style="display: none;"]')))
		time.sleep(5)
		#load_thread_no = 0
		tmp_current_thread = 0
		loop_flag = 1
		print('-------------start crawling post in category {}/{}:  {}-----------------'.format(cat_idx+1,len(self.cat_name_list),cat_name))

		thread_list = self.load_all_thread()
		#while(loop_flag):
			#thread_list = self.driver.find_elements_by_class_name("forum-nav-thread")

		#thread_list = load_thread()
		if not thread_list:
			print('no thread in this category')
		#print('     running in the {}th loop: {}th to {}th thread indx'.format(load_thread_no,tmp_current_thread+1,len(thread_list)))
		for idx in tqdm(range(len(thread_list))):
			WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "forum-nav-thread-list-wrapper")))     
			self.handling_click_cat(thread_list[tmp_current_thread])
			self.crawl_single_post(cat_name)
			self.current_thread+=1
			tmp_current_thread+=1

			#loop_flag = self.load_thread()
			#time.sleep(2)
			#load_thread_no+=1
			
		print('     all {} threads in {} category were successfully crawled\n'.format(tmp_current_thread,cat_name))
		self.driver.find_element_by_xpath('//*[@class="btn-link all-topics"]').click()
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,'//div[@class="forum-nav-browse-menu-wrapper" and @style="display: block;"]')))
		
	
	def crawl_single_post(self,cat_name):

		post_obj = self.driver.find_element_by_class_name("discussion-post")  
		try:
			post_user = self.driver.find_element_by_xpath('//*[@class="posted-details"]/a[@class="username"]').text
			nameroletypedate = self.driver.find_element_by_xpath('//*[@class="posted-details"]').text
			post_user_role = find_role(nameroletypedate)
		except:
			post_user = 'anonymous'
			post_user_role = 'n/a'


		post_timestamp = self.driver.find_element_by_xpath('//*[@class="post-header-content"]/p[@class="posted-details"]/span[@class="timeago"]').get_attribute('title')
		post_type = self.driver.find_element_by_xpath('//*[@class="posted-details"]').text.split(' ')[0]
		post_title = post_obj.find_element_by_class_name("post-title").text
		post_body = post_obj.find_element_by_class_name("post-body").text

		self.load_init_response()


		self.comment_idx = 0
		loop_flag = 1
		current_respond = 0
		while(loop_flag):
			res_obj_list = self.driver.find_elements_by_xpath('//*[@class="responses js-marked-answer-list" or @class="responses js-response-list"]/li')
			for indic,val in enumerate(res_obj_list[current_respond:]):
				
				content_dict = dict()
				usr_dict = dict()
				date_dict = dict()
				role_dict = dict()
				
				self.load_comment(val)
				content,usr,date,role = self.find_response_data(val)
				
				content_dict.update({"responses_{:02d}".format(current_respond) : content})
				usr_dict.update({"responses_{:02d}".format(current_respond):usr})
				date_dict.update({"responses_{:02d}".format(current_respond):date})
				role_dict.update({"responses_{:02d}".format(current_respond):role})

				savetextfile('tmp_content',json.dumps(content_dict,sort_keys=True, indent=4, separators=(',', ': '))[1:-2]+',')
				savetextfile('tmp_usr',json.dumps(usr_dict,sort_keys=True, indent=4, separators=(',', ': '))[1:-2]+',')
				savetextfile('tmp_date',json.dumps(date_dict,sort_keys=True, indent=4, separators=(',', ': '))[1:-2]+',')
				savetextfile('tmp_role',json.dumps(role_dict,sort_keys=True, indent=4, separators=(',', ': '))[1:-2]+',')
				
				current_respond+=1

			loop_flag = self.load_response_more()
			
		if current_respond == 0:
			post_content = {'post_category':cat_name,
							'post_timestamp':post_timestamp,
							'type':post_type,
							'title':post_title,
							'post_content':post_body,
							'post_user':post_user,
							'post_user_role':post_user_role,
						   'response':{},
						  'response_user':{},
						  'response_timestamp':{},
						  'response_role':{},
						  'No_response':current_respond,
						  'No_comment':self.comment_idx}
		else:
			post_content = {'post_category':cat_name,
							'post_timestamp':post_timestamp,
							'type':post_type,
							'title':post_title,
							'post_content':post_body,
							'post_user':post_user,
							'post_user_role':post_user_role,
						   'response':json.loads(readtextfile('tmp_content')),
						  'response_user':json.loads(readtextfile('tmp_usr')),
						  'response_timestamp':json.loads(readtextfile('tmp_date')),
						  'response_role':json.loads(readtextfile('tmp_role')),
						  'No_response':current_respond,
						  'No_comment':self.comment_idx}

		single_post = {'{:04d}'.format(self.current_thread):post_content}

		savetextfile('tmp_dis',json.dumps(single_post,sort_keys=True, indent=4, separators=(',', ': '))[1:-2]+',')

	

	
	def find_response_data(self,response_obj):
		
		total_res_content = []
		total_res_usr = []
		total_res_date = []
		total_res_role = []

		content_list = response_obj.find_elements_by_class_name("response-body")
		user_list = response_obj.find_elements_by_class_name("username")
		timestamp_list = response_obj.find_elements_by_class_name('timeago')
		response_role = find_role(response_obj.find_element_by_class_name("response-header-content").text)
		comments_res_obj = response_obj.find_elements_by_class_name("posted-details")
		
		# respond data
		total_res_content.append(content_list[0].text)
		total_res_usr.append(user_list[0].text)
		total_res_date.append(timestamp_list[0].get_attribute('title'))
		total_res_role.append(response_role)

		# comment data if available
		if len(user_list) > 0:

			for content,user,timestamp,cmt_nameroletypedate in zip(content_list[1:],user_list[1:],timestamp_list[1:],comments_res_obj[1:]):
				total_res_content.append(content.text)
				total_res_usr.append(user.text)
				total_res_date.append(timestamp.get_attribute('title'))
				total_res_role.append(find_role(cmt_nameroletypedate.text)) 
				self.comment_idx+=1

		return (total_res_content,total_res_usr,total_res_date,total_res_role)


	def close_driver(self):
		self.driver.quit()

if __name__== "__main__":
	crawler_obj = DB_crawler()
	crawler_obj.log_in()

	chosen_no = int(input('type 1 :select courses to crawl manually \nType any keys : crawl all courses listed in excel file \n : '))

	if chosen_no == 1:
		course_list  = course_selection(crawler_obj.list_dash_course())
	else:
		course_list, _ = selected_course_from_excel(crawler_obj.list_dash_course())
	
	filename = time.strftime("%Y%m%d-%H%M%S")+ "_logfile_discussion.csv"
	write_log(filename,["Course title","URL","status"])
	
	
	if Path('tmp_content').is_file():os.remove('tmp_content')
	if Path('tmp_usr').is_file():os.remove('tmp_usr')
	if Path('tmp_date').is_file():os.remove('tmp_date')
	if Path('tmp_role').is_file():os.remove('tmp_role')
	if Path('tmp_dis').is_file():os.remove('tmp_dis')
	
	

	for coursename,courseurl in zip(course_list.name,course_list.url):
		print('************************************* accessing {} course *************************************'.format(coursename))
		try:
			tmp_allcontent = crawler_obj.access_discussion(coursename,courseurl)
			dict2json = json.dumps(tmp_allcontent, sort_keys=True, indent=4, separators=(',', ': '))

			mkdir_p(Path(FOLDERDIR,clean_filename(coursename)))
			with open(Path(FOLDERDIR,clean_filename(coursename),DB_ALLDB),'w',encoding='utf-8') as f:
				f.write(dict2json)
			write_log(filename,[coursename,courseurl, 'success' ])
			
		except Exception as e:

			write_log(filename,[ coursename,courseurl, 'error {}'.format(traceback.format_exc())])
			print(traceback.format_exc())
			
	crawler_obj.close_driver()




	
	
