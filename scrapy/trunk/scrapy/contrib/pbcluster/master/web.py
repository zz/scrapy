import datetime

from pydispatch import dispatcher

from scrapy.spider import spiders 
from scrapy.management.web import banner, webconsole_discover_module
from scrapy.contrib.pbcluster.master.manager import ClusterMaster, priorities

class ClusterMasterWeb(ClusterMaster):
    webconsole_id = 'cluster_master'
    webconsole_name = 'Cluster master'

    def __init__(self):
        ClusterMaster.__init__(self)

        dispatcher.connect(self.webconsole_discover_module, signal=webconsole_discover_module)

    def webconsole_render(self, wc_request):
        changes = ""
        if wc_request.path == '/cluster_master/nodes/':
            return self.render_nodes(wc_request)
        elif wc_request.path == '/cluster_master/domains/':
            return self.render_domains(wc_request)
        elif wc_request.args:
            changes = self.webconsole_control(wc_request)

        s = self.render_header()

        s += "<h2>Home</h2>\n"

        s += "<table border='1'>\n"
        s += "<tr><th>&nbsp;</th><th>Name</th><th>Available</th><th>Running</th><th>Load.avg</th></tr>\n"
        for node in self.nodes.itervalues():
            #chkbox = "<input type='checkbox' name='shutdown' value='%s' />" % domain if node.status in ["up", "idle"] else "&nbsp;"
            nodelink = "<a href='nodes/#%s'>%s</a>" % (node.name, node.name)
            chkbox = "&nbsp;"
            loadavg = "%.2f %.2f %.2f" % node.loadavg
            s += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%d/%d</td><td>%s</td></tr>\n" % \
                 (chkbox, nodelink, node.available, len(node.running), node.maxproc, loadavg)
        s += "</table>\n"

        s += "</body>\n"
        s += "</html>\n"

        return str(s)

    def webconsole_control(self, wc_request):
        args = wc_request.args

        if "updatenodes" in args:
            self.update_nodes()

        if "schedule" in args:
            self.schedule(args["schedule"], priority=eval(args["priority"][0]))

        if "stop" in args:
            self.stop(args["stop"])

        if "remove" in args:
            self.remove(args["remove"])

        return ""

    def render_nodes(self, wc_request):
        if wc_request.args:
            self.webconsole_control(wc_request)

        now = datetime.datetime.utcnow()

        s = self.render_header()
        for node in self.nodes.itervalues():
            if node.available:
                s += "<h2><a name='%s'>%s</h2>\n" % (node.name, node.name)
        
                s += "<h3>Running domains</h3>\n"
                if node.running:
                    s += "<form method='post' action='.'>\n"
                    s += "<table border='1'>\n"
                    s += "<tr><th>&nbsp;</th><th>PID</th><th>Domain</th><th>Status</th><th>Running time</th><th>Log file</th></tr>\n"
                    for proc in node.running:
                        chkbox = "<input type='checkbox' name='stop' value='%s' />" % proc['domain'] if proc['status'] == "running" else "&nbsp;"
                        start_time = proc.get('starttime', None)
                        elapsed = now - start_time if start_time else None
                        s += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % \
                                (chkbox, proc['pid'], proc['domain'], proc['status'], elapsed, proc['logfile'])
                    s += "</table>\n"
                    s += "<input type='hidden' name='node' value='%s'>\n" % node.name
                    s += "<p><input type='submit' value='Stop selected domains on %s'></p>\n" % node.name
                    s += "</form>\n"
                else:
                    s += "<p>No running domains on %s</p>\n" % node.name

        return str(s)

    def render_domains(self, wc_request):
        if wc_request.args:
            self.webconsole_control(wc_request)

        enabled_domains = set(spiders.asdict(include_disabled=False).keys())
        print "Enabled domains: %s" % len(enabled_domains)
        inactive_domains = enabled_domains - set(self.running.keys() + [p['domain'] for p in self.pending])

        s = self.render_header()

        s += "<h2>Schedule domains</h2>\n"

        s += "Inactive domains (not running or pending)<br />"
        s += "<form method='post' action='.'>\n"
        s += "<select name='schedule' multiple='multiple' size='10'>\n"
        for domain in sorted(inactive_domains):
            s += "<option>%s</option>\n" % domain
        s += "</select>\n"
        s += "</br>\n"
        s += "Priority:<br />\n"
        s += "<select name='priority'>\n"
        for p, pname in priorities.items():
            if pname == "NORMAL":
                s += "<option value='%s' selected>NORMAL</option>" % p
            else:
                s += "<option value='%s'>%s</option>" % (p, pname)
        s += "</select>\n"
        s += "<p><input type='submit' value='Schedule selected domains'></p>\n"
        s += "</form>\n"

        s += "<h2>Domains</h2>\n"

        s += "<table border='1'>\n"
        s += "<tr><th>Domain</th><th>Status</th><th>Node</th></tr>\n"
        s += self._domains_table(self.running, '<b>running</b>')
        s += "</table>\n"

        # pending domains
        s += "<h3>Pending domains</h3>\n"
        if self.pending:
            s += "<form method='post' action='.'>\n"
            s += "<select name='remove' multiple='multiple' size='10'>\n"
            for p in self.pending:
                s += "<option value='%s'>%s (P:%s)</option>\n" % (p['domain'], p['domain'],p['priority'])
            s += "</select>\n"
            s += "<p><input type='submit' value='Remove selected pending domains'></p>\n"
            s += "</form>\n"
        else:
            s += "<p>No pending domains</p>\n"

        return str(s)

    def render_header(self):
        s = banner(self)
        s += "<p>Nav: "
        s += "<a href='/cluster_master/'>Home</a> | "
        s += "<a href='/cluster_master/domains/'>Domains</a> | "
        s += "<a href='/cluster_master/nodes/'>Nodes</a> (<a href='/cluster_master/nodes/?updatenodes=1'>update</a>)"
        s += "</p>"
        return s

    def _domains_table(self, dict_, status):
        s = ""
        for domain, node in dict_.iteritems():
            s += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n" % (domain, status, node.name)
        return s

    def webconsole_discover_module(self):
        return self