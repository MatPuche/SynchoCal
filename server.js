const express = require('express');  
const passport = require('passport');  
const GoogleStrategy = require('passport-google-oauth20').Strategy;

const app = express();  
const port = process.env.PORT || 8050;

// Serve static files
app.use(express.static(__dirname + '/public'));

// Set up passport strategy
passport.use(new GoogleStrategy(  
  {
    clientID: '432627947495-3ud93ks1aoh8b5372vjmhvcu6b05a4e3.apps.googleusercontent.com',
    clientSecret: 'p47IelIKnwEWCRDYlBTj-nHr',
    callbackURL: 'https://synchocal.herokuapp.com/auth/login',
    scope: ['email'],
  },
  // This is a "verify" function required by all Passport strategies
  (accessToken, refreshToken, profile, cb) => {
    console.log('Our user authenticated with Google, and Google sent us back this profile info identifying the authenticated user:', profile);
    return cb(null, profile);
  },
));

// Serve a test API endpoint
app.get('/auth/login', (req, res) => {  
  res.send('Your api is working!');
}); 

// This is where Google sends users once they authenticate with Google
// Make sure this endpoint matches the "callbackURL" from step 4.2 and the "authorized redirect URI" from Step 3
app.get('/auth/google/callback',  
  passport.authenticate('google', { failureRedirect: '/', session: false }),
  (req, res) => {
    console.log('wooo we authenticated, here is our user object:', req.user);
    res.json(req.user);
  }
);

// Start server
const server = app.listen(port, function() {  
  console.log('Server listening on port ' + port);
});

app.get('/auth/google', passport.authenticate('google'));  



