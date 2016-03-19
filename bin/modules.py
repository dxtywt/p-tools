#!/usr/bin/env python
import cPickle
import sys
import os
import re
import time
import glob
import getpass
import traceback

g_module_file = os.path.normcase(os.path.abspath(sys._getframe().f_code.co_filename))
g_pickle_file = os.path.splitext(g_module_file)[0] + '.pickle'
try:
    g_config = cPickle.load(open(g_pickle_file))
except:
    g_config = {}

g_user = getpass.getuser()
#g_host = os.uname()[1].replace('.baidu.com', '')
g_host = os.uname()[1]
try:
    g_crontab_time = int(g_config['config']['crontab_time'])
except:
    g_crontab_time = 300
g_origin_time = int(time.mktime(time.gmtime(0)))
g_now = int(round((time.time() - g_origin_time) / g_crontab_time)) * g_crontab_time + g_origin_time

try:
    g_idc = g_config['idc']
    g_idc_dict = {}
    for i in g_config['idc']:
        for j in g_idc[i]:
            g_idc_dict[j] = i
except:
    g_idc, g_idc_dict = {}, {}

def _uniq(s, key=None):
    return sorted(set(s), key=key)

def list_host(filter, module=None):
    if filter == 'all':
        filter = ''
    elif filter in g_idc:
        filter = '^(%s)' % '|'.join(g_idc[filter])
    regex = re.compile(filter)
    ret = []
    if 'machines' not in g_config or type(g_config['machines']) is not dict:
        return []
    for machine in g_config['machines']:
        if type(g_config['machines'][machine]) is not list:
            continue
        if regex.search(machine) and (module is None or module in g_config['machines'][machine]):
            ret.append(machine)
    return _uniq(ret, lambda x: (g_idc_dict.get(x.split('-', 1)[0]), x))

def list_ip(filter, module=None):
    import socket
    ret = []
    for machine in list_host(filter, module):
        try:
            ip = socket.gethostbyname(machine)
        except:
            ip = ''
        ret.append((machine, ip))
    return ret

def list_mobile(staff, module=None):
    ret = []
    if staff not in ('op', 'rd'):
        return []
    try:
        if staff == 'op':
            for op in g_config['staff']['op']:
                ret.append(g_config['staff']['op'][op]['mobile'])
        elif staff == 'rd':
            if module:
                for rd in g_config['modules'][module]['rd']:
                    ret.append(g_config['staff']['rd'][rd]['mobile'])
            else:
                for rd in g_config['staff']['rd']:
                    ret.append(g_config['staff']['rd'][rd]['mobile'])
    except:
        return []
    return _uniq(ret)

class _MyStr(str):
    def __repr__(self):
        return "'%s'" % self.replace("'", "\\'")

def _unicode2gbk_deep(p):
    if type(p) is dict:
        return dict((_unicode2gbk_deep(k), _unicode2gbk_deep(v)) for k, v in p.iteritems())
    elif type(p) is list:
        return list(_unicode2gbk_deep(v) for v in p)
    elif type(p) is unicode:
        return _MyStr(p.encode('gbk'))
    else:
        return p

def show(node):
    p = _unicode2gbk_deep(g_config)
    if not node.startswith('/'):
        return None
    for k in node.split('/')[1:]:
        if k == '':
            continue
        if type(p) is list and k.isdigit():
            k = int(k)
        try:
            p = p[k]
        except:
            return None
    return p

def depends(module):
    try:
        return _uniq(g_config['modules'][module]['depends'])
    except:
        return []

def rdepends(rmodule):
    ret = []
    if type(g_config['modules']) is not dict:
        return []
    for module in g_config['modules']:
        try:
            if rmodule in g_config['modules'][module]['depends']:
                ret.append(module)
        except:
            pass
    return _uniq(ret)

def update():
    import yaml
    config_file = os.path.splitext(g_module_file)[0] + '.yaml'
    fin = open(config_file)
    fout = open(g_pickle_file, 'w')
    cPickle.dump(yaml.load(unicode(fin.read(), 'gbk')), fout)
    fin.close()
    fout.close()

def _list_logs():
    ret = []
    if 'modules' not in g_config or 'machines' not in g_config or g_host not in g_config['machines']:
        return []
    for module in _uniq(g_config['machines'][g_host]):
        if module not in g_config['modules']:
            continue
        module_conf = g_config['modules'][module]
        if module_conf.get('user') != g_user or 'logs' not in module_conf:
            continue
        for log in module_conf['logs']:
            ret.append(log)
    return ret

def _do_split_log(path, old_path):
    try:
        is_same_file = os.path.samefile(path, old_path)
    except:
        is_same_file = False
    try:
        if is_same_file:
            os.remove(path)
            print '%s split_log: remove %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), path)
        else:
            if not os.path.exists(old_path):
                try:
                    open(path, 'a').close()
                    print '%s split_log: touch %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), path)
                except:
                    print '%s split_log error: cannot touch %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), path)
                    return
                os.rename(path, old_path)
                print '%s split_log: rename %s to %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), path, old_path)
    except:
        print '%s split_log: exception:' % time.strftime('%Y-%m-%d %H:%M:%S')
        traceback.print_exc(file=sys.stdout)

def _do_link_log(path, new_path):
    if os.path.exists(path) and not os.path.exists(new_path):
        try:
            os.link(path, new_path)
            print '%s split_log: link %s to %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), path, new_path)
        except:
            print '%s split_log: exception:' % time.strftime('%Y-%m-%d %H:%M:%S')
            traceback.print_exc(file=sys.stdout)

def _do_index_log(new_path, index_path):
    index_path_today = '%s.%s' % (index_path, time.strftime('%Y%m%d', time.localtime(g_now)))
    try:
        filesize = os.path.getsize(new_path)
    except:
        filesize = -1
    try:
        fout = open(index_path_today, 'a')
        print >>fout, '%s\t%s\t%d' % (time.strftime('%H:%M', time.localtime(g_now)), new_path, filesize)
        fout.close()
    except:
        print '%s index_log error: cannot write to %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), index_path_today)

def _postfix(timestamp, split_time):
    local_time = time.localtime(timestamp)
    ret = time.strftime('%Y%m%d', local_time)
    if split_time < 86400:
        ret += time.strftime('%H', local_time)
    if split_time < 3600:
        ret += time.strftime('%M', local_time)
    return ret

def split_log():
    split_list = []
    link_list = []
    index_list = []
    for log in _list_logs():
        try:
            path = log['path']
        except:
            continue
        try:
            split_time = int(log['split_time'])
            index_time = split_time
        except:
            split_time = None
            try:
                index_time = int(log['index_time'])
            except:
                index_time = None
        if index_time is None:
            if 'index_path' in log:
                index_list.append((path, log['index_path']))
            continue
        if index_time < g_crontab_time or index_time % g_crontab_time != 0:
            continue
        time_just = g_now - (g_now - g_origin_time) % index_time
        old_path = '%s.%s' % (path, _postfix(time_just - index_time, index_time))
        new_path = '%s.%s' % (path, _postfix(time_just, index_time))
        if split_time is not None:
            if time_just == g_now:
                split_list.append((path, old_path))
            link_list.append((path, new_path))
        if 'index_path' in log:
            index_list.append((new_path, log['index_path']))
    for path, old_path in _uniq(split_list):
        _do_split_log(path, old_path)
    for path, new_path in _uniq(link_list):
        _do_link_log(path, new_path)
    for new_path, index_path in _uniq(index_list):
        _do_index_log(new_path, index_path)

def _list_old_log(path, keep_days):
    ret = []
    old_time = time.mktime(time.strptime(time.strftime('%Y%m%d'), '%Y%m%d')) - keep_days * 86400
    dirname, filename = os.path.split(path)
    if not os.path.isdir(dirname) or filename == '':
        return []
    try:
        filelist = os.listdir(dirname)
    except:
        return []
    for f in filelist:
        fullpath = dirname + '/' + f
        if f.startswith(filename) and f[len(filename):len(filename)+1] == '.' \
                and f[len(filename)+1:].isdigit() and os.path.isfile(fullpath):
            try:
                if os.stat(fullpath)[8] < old_time:
                    ret.append(fullpath)
            except:
                continue
    return ret

def remove_log():
    remove_list = []
    for log in _list_logs():
        try:
            keep_days = int(log['keep_days'])
        except:
            continue
        if keep_days < 0:
            continue
        if 'path' in log:
            remove_list.extend(_list_old_log(log['path'], keep_days))
        if 'index_path' in log:
            remove_list.extend(_list_old_log(log['index_path'], keep_days))
    for path in _uniq(remove_list):
        try:
            os.remove(path)
            print "%s remove_log: remove %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), path)
        except:
            print '%s remove_log: exception:' % time.strftime('%Y-%m-%d %H:%M:%S')
            traceback.print_exc(file=sys.stdout)

def _main(argv):
    if len(argv) in (3, 4) and argv[1] in ('list', 'listip', 'listmobile'):
        filter = argv[2]
        if len(argv) == 4:
            module = argv[3]
        else:
            module = None
        if argv[1] == 'list':
            for machine in list_host(filter, module):
                print machine
        elif argv[1] == 'listip':
            for machine, ip in list_ip(filter, module):
                print "%s\t%s" % (machine, ip)
        elif argv[1] == 'listmobile':
            for mobile in list_mobile(filter, module):
                print mobile
    elif len(argv) == 3 and argv[1] == 'show':
        import curses
        import pprint
        cols = 80
        if sys.stdout.isatty():
            try:
                curses.setupterm()
                cols = curses.tigetnum('cols')
            except:
                pass
        pprint.pprint(show(argv[2]), width=cols)
    elif len(argv) == 3 and argv[1] == 'depends':
        for module in depends(argv[2]):
            print module
    elif len(argv) == 3 and argv[1] == 'rdepends':
        for module in rdepends(argv[2]):
            print module
    elif len(argv) == 2 and argv[1] == 'update':
        update()
    elif len(argv) == 2 and argv[1] == 'split_log':
        split_log()
    elif len(argv) == 2 and argv[1] == 'remove_log':
        remove_log()
    else:
        print 'Usage:'
        print '%s (list | listip) (all | filter) [module]' % argv[0]
        print '%s listmobile (op | rd) [module]' % argv[0]
        print '%s show /modules/appui/' % argv[0]
        print '%s (depends | rdepends) module' % argv[0]
        print '%s update' % argv[0]
        print '%s (split_log | remove_log)' % argv[0]

if __name__ == '__main__':
    _main(sys.argv)
