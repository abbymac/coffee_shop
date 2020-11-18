import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
Uncommenting out this line will:
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# --------------------------------------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------------------------------------


@app.route('/drinks', methods=['GET'])
def get_drinks():
    """ Get all drinks in short form from DB

        Permissions: none required, read only

        Returns:
            - 200 status code with json obj of
              short form recipe in dict.
            - Example response:
                {
                    "drinks": [
                        {
                            "id": 1,
                            "recipe": [
                                {
                                    "color": "blue",
                                    "parts": 1
                                }
                            ],
                            "title": "Water"
                        }
                    ],
                    "success": true
                }

        Raises:
            - 404 if unable to find any corresponding drink
    """

    available_drinks = Drink.query.all()
    drink_short = [drink.short() for drink in available_drinks]

    # return blank if no drinks are found, but with message
    if len(drink_short) == 0:
        print('in 0 case')
        return jsonify({
            'success': True,
            'message': 'no drinks found',
            'drinks': drink_short
        }), 200
    try:
        return jsonify({
            'success': True,
            'drinks': drink_short
        }), 200
    except Exception as error_msg:
        print(error_msg)
        abort(404)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    """ Get drink details in long form from DB

        Permissions: get:drinks-detail

        Params:
            - token [type: dict]: decoded JWT payload

        Returns:
            - 200 status code with json obj of
              long form recipe in dict
            - Example response:
                {
                    "drinks": [
                        {
                            "id": 1,
                            "recipe": [
                                {
                                    "color": "blue",
                                    "name": "water",
                                    "parts": 1
                                }
                            ],
                            "title": "Water"
                        }
                    ],
                    "success": true
                }

        Raises:
            - 404 if unable to find any corresponding drink
    """

    available_drinks = Drink.query.all()
    drink_long = [drink.long() for drink in available_drinks]

    # return blank if no drinks are found, but with message
    if not drink_long:
        return jsonify({
            'success': True,
            'message': 'no drinks found',
            'drinks': drink_long
        }), 200

    try:
        return jsonify({
            'success': True,
            'drinks': drink_long
        }), 200
    except Exception as error_msg:
        print(error_msg)
        abort(404)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_new_drink(payload):
    """ Create a drink in DB

        Permissions: post:drinks

        Params: decoded JWT payload with:
            - drink details
            - required: title and recipe
            - example post req:
                {
                    "title": "Coffee",
                    "recipe": [{
                        "name": "Coffee",
                        "color": "brown",
                        "parts": 1
                    }]
                }

        Returns:
            - Status code with json obj of
               The new recipe in long form in dict
            - Example response:
                {
                    "drinks": [
                        {
                            "id": 2,
                            "recipe": [
                                {
                                    "color": "brown",
                                    "name": "Coffee",
                                    "parts": 1
                                }
                            ],
                            "title": "Coffee"
                        }
                    ],
                    "success": true
                }

        Raises:
            - 422 if title and recipe are not given in
              payload or unable to process
    """

    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    if not title or not recipe:
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Title and recipe are required"
        }), 422
    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception as error_msg:
        print(error_msg)
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, drink_id):
    """ Edit a drink in DB

        Permissions: patch:drinks

        Params: payload, drink_id
            - payload: decoded jwt payload that has new drink details
            - drink_id: Id of drink to be edited
                - drink_id is passed through the path. Ex: /drinks/2 sends
                  patch request for drink of id=2
            - example post req:
                {
                    "title": "Decaf"
                }

        Returns:
            - Status code with json obj of
              the edited recipe in long form in dict
            - Example response:
                {
                    "drinks": [
                        {
                            "id": 2,
                            "recipe": [
                                {
                                    "color": "brown",
                                    "name": "Coffee",
                                    "parts": 1
                                }
                            ],
                            "title": "Decaf"
                        }
                    ],
                    "success": true
                }

        Raises:
            - 404 if no drink is found with corresponding drink_id
            - 422 if unable to process request
    """

    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'No drink found in database.'
        }), 404

    try:
        if title:
            drink.title = title
        if recipe:
            drink.recipe = json.dumps(recipe)
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except Exception as error_msg:
        print(error_msg)
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    """ Delete a drink with id=drink_id from DB

        Permissions: delete:drinks

        Params: payload, drink_id
            - payload: The decoded jwt payload
            - drink_id: Id of drink to be edited
                - drink_id is passed through the path. Ex: /drinks/2 sends
                  delete request for drink of id=2

        Returns:
            - Status code 200 json obj with deleted ID, message,
              and boolean success
            - Example response:
                {
                    "deleted": 2,
                    "message": "deleted",
                    "success": true
                }

        Raises:
            - 404 if no drink found with corresponding drink_id
            - 500 if unable to process delete request
    """

    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if not drink:
        abort(404)

    try:
        drink.delete()
        return jsonify({
            'message': 'deleted',
            'success': True,
            'deleted': drink_id
        }), 200
    except Exception as error_msg:
        print(error_msg)
        abort(422)

# --------------------------------------------------------------------------------------------------------
# Error Handling
# --------------------------------------------------------------------------------------------------------


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Forbidden"
    }), 403


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


@app.errorhandler(500)
def unproccesable(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal Server Error"
    }), 500


@app.errorhandler(AuthError)
def handle_auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response
