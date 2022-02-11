#coding: utf-8
#====================================================#
#  脚本名称: BTWindows_tools Version Build 20220210  #
#  脚本官网：www.btpanel.cm  技术教程：www.baota.me  #
#  QQ交流群：365208828       TG交流群：t.me/btfans   #
#====================================================#
import os,chardet,time,sys,re
import win32net, win32api, win32netcon,win32security,win32serviceutil
import traceback,shlex,datetime,subprocess,platform
import sqlite3,shutil

def readReg(path,key):
    import winreg
    try:
        newKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE ,path)
        value,type = winreg.QueryValueEx(newKey, key)
        return value
    except :
        return False
panelPath = readReg(r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\宝塔面板','PanelPath')
if not panelPath: 
    panelPath = os.getenv('BT_PANEL')
    if not panelPath: exit();

setupPath =  os.path.dirname(panelPath)
error_path = '{}/error.log'.format(setupPath)
logPath = panelPath + '/data/panelExec.log'

def mandatory_landing():
    bind_path = panelPath+ '/data/bind_path.pl'
    if os.path.exists(bind_path):os.remove(bind_path) 
    
def to_path(path):
    return path.replace('/','\\')
    
def unzip(src_path,dst_path):
    import zipfile
    zip_file = zipfile.ZipFile(src_path)  
    for names in zip_file.namelist():  
        zip_file.extract(names,dst_path)      
    zip_file.close()
    return True

def downloadFile(url,filename):
    try:
        import requests
        res = requests.get(url,verify=False)
        with open(filename,"wb") as f:
            f.write(res.content)
    except:
        import requests
        res = requests.get(url,verify=False)
        with open(filename,"wb") as f:
            f.write(res.content)


def downloadFileByWget(url,filename):
    """
    wget下载文件
    @url 下载地址
    @filename 本地文件路径
    """
    try:
        if os.path.exists(logPath): os.remove(logPath)
    except : pass
    loacl_path =  '{}/script/wget.exe'.format(panelPath)
    if not os.path.exists(loacl_path):  downloadFile('http://download.bt.cn/win/panel/data/wget.exe',loacl_path)   

    if os.path.getsize(loacl_path) < 10:
        os.remove(loacl_path)
        downloadFile(url,filename)
    else:
        shell = "{} {} -O {} -t 5 -T 60 --no-check-certificate --auth-no-challenge --force-directorie > {} 2>&1".format(loacl_path,url,filename,logPath)    
        os.system(shell)
            
        num = 0
        re_size = 0
        while num <= 5:
            if os.path.exists(filename):
                cr_size = os.path.getsize(filename)
                if re_size > 0 and re_size == cr_size:
                    break;
                else:
                    re_size = cr_size
            time.sleep(0.5)  
            num += 1

        if os.path.exists(filename):            
            if os.path.getsize(filename) < 1:
                os.remove(filename)
                downloadFile(url,filename)
        else:
            downloadFile(url,filename)

def writeFile(filename,s_body,mode='w+',encoding = 'utf-8'): 
    try:
        fp = open(filename, mode,encoding = encoding);
        fp.write(s_body)
        fp.close()
        return True
    except:
        return False
        
def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    if shell:
        cmdstring_list = cmdstring
    else:
        cmdstring_list = shlex.split(cmdstring)
    
    if timeout:
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    
    sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,shell=shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE)    
    while sub.poll() is None:
        time.sleep(0.1)
        if timeout:
            if end_time <= datetime.datetime.now():
                raise Exception("Timeout：%s"%cmdstring)
    a,e = sub.communicate()
    if type(a) == bytes: 
        try:
            a = a.decode('utf-8')
        except : 
            a = a.decode('gb2312','ignore')

    if type(e) == bytes: 
        try:
            e = e.decode('utf-8')
        except :
            e = e.decode('gb2312','ignore')
    return a,e

def update_panel(panel_v):

    ExecShell("taskkill /f /t /im BtTools.exe")

    #下载面板
    loacl_path = setupPath + '/panel.zip'
    tmpPath = "{}/temp/panel".format(setupPath)
    if os.path.exists(loacl_path): os.remove(loacl_path)   
    if os.path.exists(tmpPath): shutil.rmtree(tmpPath,True)
    if not os.path.exists(tmpPath): os.makedirs(tmpPath)

    downUrl =  'https://gitee.com/gacjie/btwindows_tools/raw/master/panel/panel_' + panel_v + '.zip';
    downloadFileByWget(downUrl,loacl_path);        
    unzip(loacl_path,tmpPath)    
    file_list = ['config/config.json','config/index.json','data/libList.conf','data/plugin.json']
    for ff_path in file_list:
        if os.path.exists(tmpPath + '/' + ff_path): os.remove(tmpPath + '/' + ff_path)  

    tcPath = '{}\class'.format(tmpPath)
    for name in os.listdir(tcPath): 
        try:              
            if name.find('win_amd64.pyd') >=0:
                oldName = os.path.join(tcPath,name);
                lName = name.split('.')[0] + '.pyd' 
                newName = os.path.join(tcPath,lName)                
                if not os.path.exists(newName):os.rename(oldName,newName)
        except :pass

    cPath = '{}/panel/class'.format(setupPath)

    if os.path.exists(cPath):            
        os.system("del /s {}\*.pyc".format(to_path(cPath)))
        os.system("del /s {}\*.pyt".format(to_path(cPath)))
        for name in os.listdir(cPath):
            try:
                if name.find('.pyd') >=0: 
                    oldName = os.path.join(cPath,name)
                    newName = os.path.join(cPath,GetRandomString(8) + '.pyt')                  
                    os.rename(oldName,newName)                    
            except : pass
        os.system("del /s {}\*.pyc".format(to_path(cPath)))
        os.system("del /s {}\*.pyt".format(to_path(cPath)))

    os.system("xcopy /s /c /e /y /r {} {}".format(to_path(tmpPath),to_path(panelPath)))    
    try:
        os.remove(loacl_path)
    except : pass

    try:
        shutil.rmtree(tmpPath,True)
    except : pass
    try:
        from gevent import monkey
    except :
        os.system('"C:\Program Files\python\python.exe" -m pip install gevent')     
    py_path = 'C:/Program Files/python/python.exe'
    ExecShell("\"{}\" {}/panel/runserver.py --startup auto install".format(py_path,setupPath))
    ExecShell("\"{}\" {}/panel/task.py --startup auto install".format(py_path,setupPath))
    os.system("bt restart")
    print("升级成功，重启面板后生效..")

def main():
    print("#====================================================#")
    print("#  脚本名称: BTWindows_tools Version Build 20220210  #")
    print("#  脚本官网：www.btpanel.cm  技术教程：www.baota.me  #")
    print("#  QQ交流群：365208828       TG交流群：t.me/btfans   #")
    print("#--------------------[实用工具]----------------------#")
    print("# (1)登陆限制[去除强制登陆的限制,720及以下版本可用]  #")
#    print("# (2)随机账号[生成随机账号信息,720及以下版本可用]    #")
    print("#--------------------[降级版本]----------------------#")
    print("# (10)7.4.0 (11)7.3.0 (12)7.2.0 (13)7.1.0 (14)7.0.0  #")
    print("#--------------------[其他功能]----------------------#")
    print("# (0)退出脚本  (0)退出脚本  (0)退出脚本  (0)退出脚本 #")
    print("#====================================================#")
    u_input = input("请输入命令编号：")
    if sys.version_info[0] == 3: u_input = int(u_input)
    if u_input == 1:
        mandatory_landing()
    elif u_input == 10:
        update_panel("7.4.0")
    elif u_input == 11:
        update_panel("7.3.0")
    elif u_input == 12:
        update_panel("7.2.0")
    elif u_input == 13:
        update_panel("7.1.0")
    elif u_input == 14:
        update_panel("7.0.0")
if __name__ == "__main__":
    main()