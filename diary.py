import hashlib
import requests
import subjects
from datetime import datetime, timedelta


def get_study_year():
    now = datetime.today()
    if now.month > 8:
        return now.year
    else:
        return now.year - 1


def getpass(p):
    return hashlib.sha1(p.encode()).hexdigest()


# Returns {bool result, string user_full_name, string user_data)
def login_account(login, password, server):
    r = requests.post(server + "login", data={'l': login, 'p': getpass(password)})
    if r.status_code == 200:
        if len(r.text) > 4:
            uid = r.text.split(',')[0]
            sid = r.text.split(',')[8][1:]
            n = r.text.split(',')[5]
            return True, n[2:len(n) - 1], login + '@' + password + '@' + uid[3:] + '@' + sid[:len(sid) - 3]
        else:
            return False, '', ''
    else:
        return False, '', ''


# Returns cookies
def get_cookies(user):
    uid = user.split('@')[2]
    login = user.split('@')[0]
    password = user.split('@')[1]
    return {'ys-userId': 'n%3A' + uid,
            'ys-user': 's%3A' + str(login.encode('unicode_escape')).replace('b\'', '').replace('\'', '').replace("\\\\",
                                                                                                                 "%").upper().replace(
                'U', 'u'),
            'ys-password': 's%3A' + getpass(password)}


# Returns class id
def get_student_class(user, server):
    sid = user.split('@')[3]
    now = datetime.today()
    c = get_cookies(user)
    r = requests.post(server + 'act/GET_STUDENT_CLASS',
                      data={'currentDate': '{}.{}.{}'.format(now.day, now.month, now.year), 'student': sid,
                            'uchYear': get_study_year(), 'uchId': '1'},
                      cookies=c)
    cid = str(r.text).split(',')[0]
    cid = cid[3:len(cid)]
    return cid


# Parses student homework
def parse_student_homework(s):
    week = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday']
    hlist = {}
    ss = s.split('\n')
    ss.pop(0)
    ss.pop(len(ss) - 1)
    for l in ss:
        d = l.lstrip().split(' ')[1]
        d = d.replace('Date(', '')
        d = d.split(',')[:3]
        day = d[2]
        month = d[1]
        year = d[0]
        date = str(day + '.' + str(int(month) + 1) + '.' + year)
        date += ' ' + week[datetime.strptime(date, '%d.%m.%Y').weekday()]
        hw = l.replace('\\\"', '').split('\"');
        if (len(hw) > 3):
            hw = l.replace('\\\"', '').split('\"')[3].replace('\\n', ' | ')
        else:
            hw = ''
        if len(hw) < 1:
            continue
        if len(hw) > 200:
            hw = hw[:200] + '...'
        s = int(l.lstrip().split(' ')[3].replace(',', ''))
        if date not in hlist:
            hlist[date] = ''
        hlist[date] += '#' + subjects.subject[s].replace(' ', '_').replace('-', '_') + ' ' + hw + '\n'

    result = ''
    lastdate = ''
    for date, hw in hlist.items():
        if date != lastdate:
            result += '\n' + date + '\n'
        result += hw
        result += '\n'
        lastdate = date
    return result


def get_student_homework(user, period, from_date, server):
    sid = user.split('@')[3]
    begin = from_date - timedelta(days=period)
    c = get_cookies(user)
    r = requests.post(server + 'act/GET_STUDENT_DAIRY',
                      # really??? DAIRY???? this was the problem I couldn't find????
                      data={'pClassesIds': '', 'student': sid, 'cls': get_student_class(user, server),
                            'begin_dt': '{}.{}.{}'.format(begin.day, begin.month, begin.year),
                            'end_dt': '{}.{}.{}'.format(from_date.day, from_date.month, from_date.year)},
                      cookies=c)
    if r.status_code == 200 and len(r.text) > 2:
        return True, parse_student_homework(r.text)
    else:
        return False, ''


def get_current_quarter_start():
    now = datetime.today()
    if now.month < 4:
        # 3 quarter
        return datetime(year=now.year, month=1, day=14)
    elif 4 <= now.month < 6:
        # 4 quarter
        return datetime(year=now.year, month=4, day=1)
    elif 8 < now.month < 11:
        # 1 quarter
        return datetime(year=now.year, month=9, day=1)
    elif 11 <= now.month:
        # 2 quarter
        return datetime(year=now.year, month=11, day=6)
    return datetime(year=now.year, month=1, day=1)


def parse_student_journal(s, begin):
    marks = {}
    ss = s.split('\n')
    ss.pop(0)
    ss.pop(len(ss) - 1)
    for l in ss:
        mark = l.lstrip().split(' ')[2][1]
        date = l.lstrip().split(' ')[4].replace('Date', '').split(',')
        year = int(date[0].replace('(', ''))
        month = int(date[1]) + 1
        day = int(date[2])
        subj = int(l.lstrip().split(' ')[5].replace(',', ''))
        if year < begin.year or (year < begin.year and month < begin.month) or (
                year < begin.year and month < begin.month and day < begin.day):
            continue
        subj = subjects.subject[subj].replace(' ', '_').replace('-', '_')
        if subj not in marks:
            marks[subj] = ''
        marks[subj] += mark + ' '

    result = ''
    for subj, m in marks.items():
        result += '#' + subj + ' ' + m + '\n'
    return result


def get_student_journal(user, server):
    sid = user.split('@')[3]
    begin = get_current_quarter_start()
    c = get_cookies(user)
    r = requests.post(server + 'act/GET_STUDENT_JOURNAL_DATA',
                      data={'parallelClasses': '', 'student': sid, 'cls': get_student_class(user, server)},
                      cookies=c)
    if r.status_code == 200 and len(r.text) > 2:
        return True, parse_student_journal(r.text, begin)
    else:
        return False, ''
