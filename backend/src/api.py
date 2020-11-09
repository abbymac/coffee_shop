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
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

## ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    available_drinks = Drink.query.all()
    drink_short = [drink.short() for drink in available_drinks]
    print('d', drink_short)

    if len(drink_short) == 0:
        abort(404)
    try: 
        return jsonify({
            'success': True,
            'drinks': drink_short
        }), 200
    except: 
        abort(404)
    



@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(token):
    available_drinks = Drink.query.all()
    drink_long = [drink.long() for drink in available_drinks]
    
    if not drink_long: 
        abort(404)
    
    try: 
        return jsonify({
            'success': True, 
            'drinks': drink_long
        }), 200
    except: 
        abort(404)




@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_new_drink(payload):
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    print('title', title)
    print('recipte', recipe)

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

    except:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, drink_id):
    print('in patch')
    if not drink_id: 
        abort(404)

    body = request.get_json()
    print('body is', body)
    title = body.get('title', None)
    recipe = body.get('recipe', None)
    print('recipe is', recipe)
    print('title is', title)
    print('id is', drink_id)

    # if not title or not recipe:
    #     return jsonify({
    #         "success": False,
    #         "error": 422,
    #         "message": "Title and recipe are required"
    #     }), 422
    drink = Drink.query.filter(Drink.id==drink_id).one_or_none()
    if drink is None: 
        return jsonify({
            'success': False, 
            'error': 404, 
            'message': 'No drink found in database.'
        }), 404

    try: 
        if title: 
            print('in title', title)
            drink.title = title 
        if recipe:
            drink.recipe = json.dumps(recipe)
        print('ttttt')
        print('drink now', drink)
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except: 
        abort(422)



@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    
    if not drink_id:
        abort(404)

    try: 
        drink = Drink.query.get(drink_id)
        drink.delete()
        return jsonify({
            'message': 'deleted',
            'success': True, 
            'deleted': drink_id
        }), 200
    except: 
        abort(500)
  

      
# --------------------------------------------------------------------------------------------------------
## Error Handling
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