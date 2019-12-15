"""
Taken from 
  http://appengine-cookbook.appspot.com/recipe/restrict-application-to-an-authorized-set-of-users/
"""
import os

import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
import logging

class AuthorizedUser(db.Model):
    """Represents authorized users in the datastore."""
    user = db.UserProperty()
    canWrite = db.BooleanProperty(default=True)


def findAuthUser(email):
    """Return AuthorizedUser for `email` or None if not found."""
    user = users.User(email)
    auth_user =  AuthorizedUser.gql("where user = :1", user).get()
    logging.debug("findAuthUser(%r) = %s" % (email, auth_user))
    return auth_user
    

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class AuthorizedRequestHandler(webapp2.RequestHandler):
    """Authenticate users against a stored list of authorized users.

    Base your request handler on this class and check the authorize() method
    for a True response before processing in get(), post(), etc. methods.

    For example:

    class Test(AuthorizedRequestHandler):
        def get(self):
            if self.authorize():
                self.response.out.write('You are an authenticated user.')
    """
    
    def authorize(self):
        """Return True if user is authenticated."""
        user = users.get_current_user()
        if not user:
            self.not_logged_in()
        else:
            auth_user = AuthorizedUser.gql("where user = :1", user).get()
            if not auth_user:
                self.unauthorized_user()
            else:
                return True

    def not_logged_in(self):
        """Action taken when user is not logged in (default: go to login screen)."""
        self.redirect(users.create_login_url(self.request.uri))

    def unauthorized_user(self):
        """Action taken for unauthenticated  user (default: go to error page)."""
        self.response.out.write("""
            <html>
              <body>
                <div>Unauthorized User</div>
                <div><a href="%s">Logout</a>
              </body>
            </html>""" % users.create_logout_url(self.request.uri))


class ManageAuthorizedUsers(webapp2.RequestHandler):
    """Manage list of authorized users through web page.

    The GET method shows page with current list of users and allows
    deleting user or adding a new user by email address.

    The POST method handles adding a new user.
    """

    template_file = 'auth.html'
    
    def get(self):
        template_values = {
            'authorized_users': AuthorizedUser.all()
            }
        template = JINJA_ENV.get_template(self.template_file)
        self.response.out.write(template.render(template_values))

    def post(self):
        email = self.request.get('email')
        user = users.User(email)
        auth_user = AuthorizedUser()
        auth_user.user = user
        if self.request.get('write'):
            auth_user.canWrite = True
        else:
            auth_user.canWrite = False
        auth_user.put()
        self.redirect('/auth/users?updated')


class DeleteAuthorizedUser(webapp2.RequestHandler):
    """Delete an authorized user from the datastore."""
    def get(self):
        email = self.request.get('email')
#        print 'email: ', email
        user = users.User(email)
        auth_user = AuthorizedUser.gql("where user = :1", user).get()
        auth_user.delete()
        self.redirect('/auth/users?deleted')


app = webapp2.WSGIApplication([('/auth/users', ManageAuthorizedUsers),
                               ('/auth/useradd', ManageAuthorizedUsers),
                               ('/auth/userdelete', DeleteAuthorizedUser)],
                              debug=True)

def main():
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
