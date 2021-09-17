#!/usr/bin/env python3

import sys, os, subprocess, re, datetime
import mechanicalsoup
import traceback

class Course: # {{{
    def __init__(self):
        self.name     = None
        self.play     = None
        self.detail   = None
        self.cert     = None
        self.until    = None
        self.absolved = None

    def load_tr(self, tr, until_n = 0, since_n = 0): # {{{

        for td in tr.select('td:nth-child(2)'):
            self.name = td.text.strip()

        for a in tr.select('td.kurz-play a, td.kurz-replay a'):
            try:
                m = re.match(r"window\.open\s*\(\s*'(../kurzy-(?:story|scorm)[^']*)'", a['onclick'])
                if m:
                    self.play = m.group(1)
            except KeyError:
                pass

        for span in tr.select('td.detail-info span'):
            try:
                self.detail = span['jsparam']
            except KeyError:
                pass

        for a in tr.select('a.kurz-certifikat'):
            try:
                self.cert = a['href']
            except KeyError:
                pass

        if until_n > 0:
            for td in tr.select('td:nth-child(%d)' % until_n):
                self.until = td.text.strip()

        if since_n > 0:
            for td in tr.select('td:nth-child(%d)' % since_n):
                self.absolved = td.text.strip()

        return self
    # }}}

    def __str__(self):
        return "kurz: %(name)s\n  do: %(until)s\n  url: %(play)s\n  kdy: %(absolved)s\n  cert: %(cert)s" % self.__dict__

    def absolved_date(self): # {{{
        if self.absolved is None:
            return None
        return datetime.date(*[ int(x) for x in reversed(self.absolved.split('.'))])
    # }}}

    def get_course_id(self): # {{{
        if self.play:
            x = self.play.split('/')
            assert len(x[-1]) == 0 and len(x[-2]) > 0
            return x[-2]
        if self.cert:
            m = re.match(r'name=([^=&]*)&', self.cert)
            return m.group(1)
        assert False
    # }}}
# }}}

class Instructor: # {{{
    URL='https://lms.instructor.cz'

    def __init__(self):
        self.s = mechanicalsoup.StatefulBrowser()
        self.active_courses = []
        self.passed_courses = []

    def get_active_courses(self, response=None): # {{{
        self.active_courses = []
        if response is None:
            s = self.s
            response = s.open(self.URL + '/user/u_objednane.aspx')
            assert 200 <= response.status_code < 300

        for course_tr in response.soup.select("tr:has(td.kurz-play)"):
            self.active_courses.append(Course().load_tr(course_tr, until_n = 4))
            #print(self.active_courses[-1])

        return self.active_courses
    # }}}

    def get_passed_courses(self, response=None): # {{{
        self.passed_courses = []
        if response is None:
            s = self.s
            response = s.open(self.URL + '/user/u_absolvovane.aspx')
            assert 200 <= response.status_code < 300

        for course_tr in response.soup.select("tr:has(a.kurz-certifikat)"):
            self.passed_courses.append(Course().load_tr(course_tr, since_n = 1))
            #print(self.passed_courses[-1])

        return self.passed_courses
    # }}}

    def login_get_courses(self, user, password): # {{{
        s = self.s
        r = s.open(self.URL + '/user/')
        assert 200 <= r.status_code < 300

        s.select_form('form[action="./"]')
        s["tbLogin"]    = user
        s["tbPassword"] =  password
        r = s.submit_selected()
        assert 200 <= r.status_code < 300
        return self.get_active_courses(r)
    # }}}

    def do_course(self, course): # {{{
        print("Absolvuji", course)
        s = self.s
        r = s.open('https://lms.instructor.cz/user/test/default1.aspx?name=%s' % (course.get_course_id()))
        if 'specifika' in s.get_url():
            print("Specifika:")
            for a in r.soup.select('a'):
                print(" ",a)
            print("Potvrzuji...")
            s.select_form('form')
            r = s.submit_selected()
        assert "test/default1.aspx" in s.get_url()
        if len(r.soup.select("table.question")) > 3:
            s.select_form('form')
            referer = s.get_url()
            r = s._request(
                s.get_current_form().form,
                s.get_url(),
                headers={"Referer": s.get_url()}
            )
            s.add_soup(r, s.soup_config)
            for q in r.soup.select("table.question"):
                for td in q.select("table.questionText td"):
                    print(td.text.strip())
                for tr in q.select("table.answers tr"):
                    for i in tr.select("input"):
                        name  = i["name"]
                        value = i["value"]
                    prefix = " - "
                    for p in tr.select("p"):
                        if "right" in p.get("class",''):
                            prefix = " * "
                            s[name] = value
                        print(prefix + p.text.strip())
        elif len(r.soup.select("div.mainFrame input.end")) > 0:
            s.select_form('#form1')
        else:
            raise Exception("Unsupported course.")

        r = s.submit_selected()
        if 200 <= r.status_code < 300:
            print("Success")
    # }}}
# }}}

def main(argv): # {{{
    if len(argv) > 0:
        if argv[0] == 'pass':
            user_pass = subprocess.check_output(argv).decode('utf-8')
            n = 0
            for line in user_pass.split('\n'):
                if not n:
                    password = line.strip()
                else:
                    m = re.match(r'^\s*[Uu]ser(?:name)?\s*[:=]\s*(.*)$', line)
                    if m:
                        username = m.group(1).strip()
                n = n+1
        else:
            print("usage: %s [pass ZX2C4_PASSWORD_PATH]" % sys.argv[0])
            print("\nTries to active courses and downloads certificates of courses finished in past 7 days")
            sys.exit(1)
    else:
        sys.stdout.write("Username: ")
        sys.stdout.flush()
        username = input()
        sys.stdout.write("Password: ")
        sys.stdout.flush()
        password = input()

    I = Instructor()
    todo = I.login_get_courses(username, password)

    for c in todo:
        try:
            I.do_course(c)
        except Exception:
            print("Failure")
            traceback.print_exc()

    last_week = datetime.date.today() - datetime.timedelta(7)
    for c in I.get_passed_courses():
        # Note we have correct url in I
        if c.absolved_date() >= last_week:
            dl_to   = "%s %s.pdf" % (c.absolved_date(), c.name)
            dl_from = I.s.absolute_url(c.cert)
            print("Download %s -> %s" % (dl_from, dl_to))
            resp = I.s.session.get(dl_from)
            assert 200 <= resp.status_code < 300
            assert resp.headers['Content-Type'] == 'application/pdf'
            with open(dl_to, "wb") as f:
                f.write(resp.content)
    print("Done")
# }}}

main(sys.argv[1:])
