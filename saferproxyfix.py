class SaferProxyFix(object):
    def __init__(self, app, num_proxy_servers=1, detect_misconfiguration=False):
        self.app = app
        self.num_proxy_servers = num_proxy_servers
        self.detect_misconfiguration = detect_misconfiguration

    def get_remote_addr(self, forwarded_for):
        if self.detect_misconfiguration and not forwarded_for:
            raise Exception("SaferProxyFix did not detect a proxy server. Do not use this fixer if you are not behind a proxy.")
        if self.detect_misconfiguration and len(forwarded_for) < self.num_proxy_servers:
            raise Exception("SaferProxyFix did not detect enough proxy servers. Check your num_proxy_servers setting.")
            
        if forwarded_for and len(forwarded_for) >= self.num_proxy_servers:
            return forwarded_for[-1 * self.num_proxy_servers]

    def __call__(self, environ, start_response):
        getter = environ.get
        forwarded_proto = getter('HTTP_X_FORWARDED_PROTO', '')
        forwarded_for = getter('HTTP_X_FORWARDED_FOR', '').split(',')
        forwarded_host = getter('HTTP_X_FORWARDED_HOST', '')
        environ.update({
            'werkzeug.proxy_fix.orig_wsgi_url_scheme':  getter('wsgi.url_scheme'),
            'werkzeug.proxy_fix.orig_remote_addr':      getter('REMOTE_ADDR'),
            'werkzeug.proxy_fix.orig_http_host':        getter('HTTP_HOST')
        })
        forwarded_for = [x for x in [x.strip() for x in forwarded_for] if x]
        remote_addr = self.get_remote_addr(forwarded_for)
        if remote_addr is not None:
            environ['REMOTE_ADDR'] = remote_addr
        if forwarded_host:
            environ['HTTP_HOST'] = forwarded_host
        if forwarded_proto:
            environ['wsgi.url_scheme'] = forwarded_proto
        return self.app(environ, start_response)