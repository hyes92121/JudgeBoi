var axios = require('axios');
var express = require('express');
var cors = require('cors');
var app = express();

const GITHUB_AUTH_ACCESSTOKEN_URL = 'https://github.com/login/oauth/access_token';
const CLIENT_ID = 'd594b1e3ed003d5124af';
const CLIENT_SECRET = '6d3f8133224c8b44ab7cb99ee447a25471a32e99';

app.use(cors());

app.get('/api/access_token', function (req, res) {
    const CODE = req.query.code

    axios({
        method: 'post',
        url: GITHUB_AUTH_ACCESSTOKEN_URL,
        data: {
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            code: CODE
        },
        headers: {
            Accept: 'application/json'
        }
    })
    .then(function (response) {
        res.send({
            data: response.data
        })
        console.log('Success')
    })
    .catch(function (error) {
        console.error('Error ' + error.message)
    })
});

app.listen(3000, function () {
    console.log('GithubOAuthProxy listening on port 3000!');
});