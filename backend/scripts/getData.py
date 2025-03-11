# Port: 5000
# Routes: /getAccountRequests (GET), /getCountries (GET), /getListings (GET), /getListingsByIDs (POST), /getListing/<id> (GET), /getProducers (GET), /getProducer/<id> (GET), /getRandomListings (GET),
#           /getRecentListingReviews/<id> (GET), /getAllListingsNames (GET), /getBookmarkListings (POST), /getUserReviewSummary/<id> (GET),
#           /getReviews (GET), /getReviewByTarget/<id> (GET), /getReviewsByUserIds (GET), /getProducerTourReviews (GET), /getUsers (GET), /getUser/<id> (GET), 
#           /getUserPhoto/<id>/<userType> (GET), /getUserByUsername/<username> (GET), /getVenues (GET),
#           /getVenue/<id> (GET), /getVenuesAPI (GET), /getDrinkTypes (GET), /getRequestListings (GET), /getRequestListing/<id> (GET), /getRequestEdits (GET), 
#           /getRequestEdit/<id> (GET), /getModRequests (GET), /getFlavourTags (GET), /getSubTags (GET), /getObservationTags (GET), /getColours (GET), 
#           /getSpecialColours (GET), /getLanguages (GET), /getServingTypes (GET), /getProducersProfileViews (GET), /getVenuesProfileViewsByVenue/<id> (GET), /getRequestInaccuracyByVenue/<id> (GET)
#           /getUserFollowList/<id> (GET), /getUserNames (GET), /checkFollowing/<userId>/<userType>/<followId>/<followType> (GET) /getLatestNews (GET)
# -----------------------------------------------------------------------------------------

# pip install python-bsonjs
# pip install Flask
# pip install Flask Flask-PyMongo
# pip install pymongo
# pip install flask-cors

import os
import json
import random
from bson import json_util, ObjectId
from flask import Blueprint, g, jsonify, request
from bson.objectid import ObjectId
from psycopg2.extras import RealDictCursor
import random
import feedparser
import re
import requests
import psycopg2.extras
from bs4 import BeautifulSoup


file_name = os.path.basename(__file__)
blueprint = Blueprint(file_name[:-3], __name__)

# clean up html tags
def clean_html(html):
    """Remove HTML tags and extract plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")  # Extract plain text with spaces instead of HTML tags
    
    text = text.replace("\\n", "\n")  # Replace escaped '\n' with actual new lines
    text = text.replace('\\"', '"')  # Replace escaped quotes with actual quotes
    text = text.replace("\\'", "'")  # Replace escaped single quotes (if needed)
    text = re.sub(r'\\+', '', text)  # Remove any remaining backslashes
    text = re.sub(r'\s+', ' ', text).strip()  # Remove excessive spaces
    
    return text

# # converts 88 bamboo atom rss to JSON
def parse_rss(rss_url):
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return {"error": "Invalid RSS feed or no entries found."}

    rss_data = {
        "feed": {
            "title": feed.feed.get("title", "No title"),
            "link": feed.feed.get("link", "No link"),
            "description": feed.feed.get("subtitle", "No description"),
            "language": feed.feed.get("language", "Unknown"),
            "updated": feed.feed.get("updated", "Unknown date"),
            "author": feed.feed.get("author", "Unknown author")
        },
        "entries": []
    }

    for entry in feed.entries:
        formatted_entry = {
            "title": entry.get("title", "No title"),
            "link": entry.get("link", "No link"),
            "published": entry.get("published", "Unknown date"),
            "summary": clean_html(entry.get("summary", "No summary")), 
            "author": entry.get("author", "Unknown author"),
            "categories": [tag.term for tag in entry.get("tags", [])] if "tags" in entry else [],
            "content": clean_html(entry.get("content", [{"value": ""}])[0]["value"] if "content" in entry else ""),  
        }
        rss_data["entries"].append(formatted_entry)

    return rss_data

def get_og_image(url):
    """Extract Open Graph image from a given article URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}  # Prevent bot-blocking
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        og_image = soup.find("meta", property="og:image")

        if og_image and og_image.get("content"):
            return og_image["content"]
        return None  # No OG image found
    except requests.exceptions.RequestException:
        return None  # Request failed

# converts BSON to JSON
def parse_json(data):
    return json.loads(json_util.dumps(data))

# Helper function to fetch user data from the database
def fetch_user_data(cursor, user_id):
    cursor.execute('SELECT * FROM "users" WHERE "id" = %s', (user_id,))
    return cursor.fetchone()

# Helper function to fetch drink lists for a user
def fetch_drink_lists(cursor, user_id):
    # First, get all drink lists for the user
    cursor.execute("""
        SELECT "id", "listName"
        FROM "usersDrinkLists"
        WHERE "userId" = %s
    """, (user_id,))
    
    drink_lists_data = cursor.fetchall()
    result = {}

    for row in drink_lists_data:
        list_id = row["id"]
        list_name = row["listName"]

        # Initialize the list in the result dictionary
        result[list_name] = {
            "listDesc": "",  # Customize or fetch descriptions if needed
            "listItems": [],
        }

        # Fetch the drinks for this list, along with their addedDate
        cursor.execute("""
            SELECT "drinkId", "addedDate"
            FROM "usersDrinkListItems"
            WHERE "listId" = %s
            ORDER BY "addedDate" DESC
        """, (list_id,))
        
        drinks_data = cursor.fetchall()

        # Add drinks to the list
        result[list_name]["listItems"] = [
            {"drinkId": row["drinkId"], "addedDate": row["addedDate"]}
            for row in drinks_data
        ]

    return result

# Helper function to fetch follow lists for a user
def fetch_follow_lists(cursor, user_id):
    cursor.execute("""
        SELECT "users", "producers", "venues"
        FROM "usersFollowLists"
        WHERE "userId" = %s
    """, (user_id,))
    follow_lists_data = cursor.fetchone()
    
    return {
        "users": follow_lists_data["users"] if follow_lists_data and follow_lists_data["users"] else [],
        "producers": follow_lists_data["producers"] if follow_lists_data and follow_lists_data["producers"] else [],
        "venues": follow_lists_data["venues"] if follow_lists_data and follow_lists_data["venues"] else []
    }

# Helper function to fetch venue menu items based on venueId
def fetch_venue_listings(cursor, venue_id):
    cursor.execute("""
        SELECT * 
        FROM "listings" 
        WHERE "id" IN (
            SELECT mi."itemID"
            FROM "menuItems" mi
            JOIN "venuesMenu" vm ON mi."sectionId" = vm."id"
            WHERE vm."venueId" = %s
        );
    """, (venue_id,))
    venue_items = cursor.fetchall()

    return venue_items

# def modifyPhotos():
#     data = db.producers.find({})
#     dataEncode = parse_json(data)
#     for doc in dataEncode:
#         try:
#             if(doc['photo']):
#                 photo = s3Images.uploadBase64ImageToS3(doc['photo'])
#                 updateImage = db.producers.update_one({'_id': ObjectId(doc['_id']['$oid'])}, {'$set': {'photo': photo, 'updates': []}})
#         except Exception as e:
#             print(e)
#         print(doc['_id'])

# modifyPhotos()

# -----------------------------------------------------------------------------------------
# [GET] accountRequests
@blueprint.route('/getAccountRequests', methods=['GET'])
def getAccountRequests():
    conn = g.db
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "accountRequests"')
        allAccountRequests = cursor.fetchall()

    if not allAccountRequests:
        return jsonify([])

    return jsonify(allAccountRequests)

# -----------------------------------------------------------------------------------------
# [GET] Countries
@blueprint.route('/getCountries', methods=['GET'])
def getCountries():
    conn = g.db
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM countries")
        allCountries = cursor.fetchall()

    if not allCountries:
        return jsonify([])
    
    return jsonify(allCountries)

# -----------------------------------------------------------------------------------------
# [GET] Listings
@blueprint.route("/getListings")
def getListings():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings"')
        listings_data = cursor.fetchall()
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)


#  [GET] ALL Listing Names in Listing Table
@blueprint.route("/getListingsName")
def getListingsName():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings"')
        listingsName_data = cursor.fetchall()
    
    if not listingsName_data:
        return jsonify([])
    
    # Extract listingName from each record
    listing_names = [listing['listingName'] for listing in listingsName_data]

    return jsonify(listing_names)

# [POST] Listings by IDs
@blueprint.route("/getListingsByIDs", methods=['POST'])
def getListingsByIDs():
    conn = g.db

    listing_ids = request.json.get('listingIDs', [])

    if not listing_ids:
        return jsonify([]), 404

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings" WHERE "id" IN %s', (tuple(listing_ids),))
        listings_data = cursor.fetchall()
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] Get Listings from a randomly selected date
@blueprint.route("/getRandomListings")
def getRandomListings():
    conn = g.db

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Fetch distinct dates by converting timestamps to dates
        cursor.execute('SELECT DISTINCT "addedDate"::DATE FROM "listings"')
        date_results = cursor.fetchall()

        if not date_results:
            return jsonify({"error": "No dates found in listings"}), 400

        # Log the fetched dates
        print("Fetched date_results:", date_results)

        try:
            # Extract 'addedDate' values properly from RealDictRow
            date_list = [row['addedDate'] for row in date_results if 'addedDate' in row]
            
            # Log the extracted date list
            print("Extracted date_list:", date_list)

            if not date_list:
                return jsonify({"error": "Date extraction failed (empty list)"}), 400

            random_date = random.choice(date_list)  # Select a random date
        except Exception as e:
            return jsonify({"error": f"Random selection failed: {str(e)}"}), 500

        # Fetch listings from the selected random date
        cursor.execute('SELECT * FROM "listings" WHERE "addedDate"::DATE = %s ORDER BY RANDOM() LIMIT 30', (random_date,))
        listings_data = cursor.fetchall()

    if not listings_data:
        return jsonify({"error": "No listings found for selected date"}), 400

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] Get Listings from db where id> last item in list
@blueprint.route("/getNext30/<id>")
def getNext30(id):
    conn = g.db
    id = int(id)
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings" where "id" > %s LIMIT 30', (id,))
        listings_data = cursor.fetchall()
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# Testing Next 30 randomised
# @blueprint.route("/getNext30random/<int:id>")
# def getNext30random(id):
#     conn = g.db

#     with conn.cursor() as cursor:
#         # 1️⃣ Get the date of the given listing ID
#         cursor.execute('SELECT "addedDate" FROM "listings" WHERE "id" = %s', (id,))
#         date_result = cursor.fetchone()

#         if not date_result:
#             return jsonify({"error": "Listing not found"}), 404

#         listing_date = date_result[0]  # Extract the date

#         # 2️⃣ Get the next 30 listings from the same date
#         cursor.execute('''
#             SELECT * FROM "listings" 
#             WHERE "addedDate"::DATE = %s AND "id" > %s 
#             ORDER BY "id" ASC 
#             LIMIT 30
#         ''', (listing_date, id))

#         listings_data = cursor.fetchall()

#     if not listings_data:
#         return jsonify([])  # Return an empty list if no more listings are found

#     return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] Listings from db when filter is applied for next 30 in discovery tab
@blueprint.route("/getFiltered30/<id>")
def getFiltered30(id):
    conn = g.db
    id = int(id)
    drinkType= request.args.get('drinkType')  # e.g. ?age=30
    drinkCategory = request.args.get('drinkCategory')
    
    with conn.cursor() as cursor:
        if(drinkType and drinkCategory):
            cursor.execute('SELECT * FROM "listings" where "id" > %s AND "drinkType" = %s AND "typeCategory" = %s LIMIT 30', (id,drinkType,drinkCategory,))
        elif(drinkType):
            cursor.execute('SELECT * FROM "listings" where "id" > %s AND "drinkType" = %s LIMIT 30', (id,drinkType,))      
        else:
            cursor.execute('SELECT * FROM "listings" where "id" > %s LIMIT 30', (id,))
        listings_data = cursor.fetchall()
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] Get Listings from next in following list for both venue and producer
@blueprint.route("/getNextFollowing30/<id>")
def getNextFollowing30(id):
    conn = g.db
    id = int(id)

    followedProducers = request.args.get('followedProducers').replace('[', '').replace(']', '').replace('"', '').split(',')
    followedVenues = request.args.get('followedVenues')
    
    # Make sure followedProducers is a tuple so SQL can process
    placeholders = ', '.join(['%s'] * len(followedProducers))

    with conn.cursor() as cursor:
        query = f'SELECT * FROM "listings" WHERE "id" > %s AND "producerID" IN ({placeholders}) LIMIT 30'
        params = (id, *followedProducers)
        cursor.execute(query, params)
        listings_data = cursor.fetchall()
        if followedVenues != '"null"':
            
            venue_listings = fetch_venue_listings(cursor, followedVenues.replace('"',''))
            listings_data += venue_listings
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] Listings from db when filter is applied for next 30 in following tab
@blueprint.route("/getFilteredFollowing30/<id>")
def getFilteredFollowing30(id):
    conn = g.db
    id = int(id)
    drinkType= request.args.get('drinkType')  # e.g. ?age=30
    drinkCategory = request.args.get('drinkCategory')
    
    with conn.cursor() as cursor:
        if(drinkType and drinkCategory):
            cursor.execute('SELECT * FROM "listings" where "id" > %s AND "drinkType" = %s AND "typeCategory" = %s LIMIT 30', (id,drinkType,drinkCategory,))
        elif(drinkType):
            cursor.execute('SELECT * FROM "listings" where "id" > %s AND "drinkType" = %s LIMIT 30', (id,drinkType,))      
        else:
            cursor.execute('SELECT * FROM "listings" where "id" > %s LIMIT 30', (id,))
        listings_data = cursor.fetchall()
    
    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------
# [GET] For You Page Recommender
# helper function for basic algo
def basic_algo(userID):
    conn = g.db
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Fetch user's drink choice, flavour choice, and preferences
        cursor.execute(
            'SELECT "choiceDrinks", "choiceFlavours", "preferences" FROM users WHERE id = %s',
            (userID,)
        )
        user_data = cursor.fetchone()

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        choiceDrink = user_data["choiceDrinks"] or []
        choiceFlavour = user_data["choiceFlavours"] or []
        preferences = user_data["preferences"] or []
        print("User Data:", user_data)

        recommended = {}

        # Get listings with the same drink type
        if choiceDrink:
            drink_query = '''
                SELECT * FROM listings 
                WHERE "drinkType" = ANY(%s)
            '''
            cursor.execute(drink_query, (choiceDrink,))
            drink_listings = cursor.fetchall()

            for listing in drink_listings:
                if listing["id"] not in recommended:
                    recommended[listing["id"]] = listing 

        # Get listings with the same flavour tags
        if choiceFlavour:
            cursor.execute('SELECT id FROM "subTags" WHERE "subTag" = ANY(%s)', (choiceFlavour,))
            flavour_ids = [row["id"] for row in cursor.fetchall()]

            if flavour_ids:
                flavour_query = '''
                    SELECT DISTINCT l.*
                    FROM "listings" l
                    JOIN "reviews" r ON l."id" = r."reviewTarget"
                    WHERE r."flavourTag" && %s::text[]
                '''
                cursor.execute(flavour_query, (flavour_ids,))
                flavour_listings = cursor.fetchall()

                for listing in flavour_listings:
                    if listing["id"] not in recommended:
                        recommended[listing["id"]] = listing

        # Get listings with the same observation tags
        if preferences:
            observation_query = '''
                SELECT DISTINCT l.*
                FROM "listings" l
                JOIN "reviews" r ON l."id" = r."reviewTarget"
                WHERE r."observationTag" && %s::text[]
            '''
            cursor.execute(observation_query, (preferences,))
            observation_listings = cursor.fetchall()

            for listing in observation_listings:
                    if listing["id"] not in recommended:
                        recommended[listing["id"]] = listing

        query = """
        SELECT DISTINCT l.*
        FROM "listings" l
        LEFT JOIN "reviews" r ON l."id" = r."reviewTarget"
        LEFT JOIN "subTags" st ON r."flavourTag" && ARRAY[st.id]::text[]
        WHERE 
            l."drinkType" = ANY(%s) OR 
            r."flavourTag" && %s::text[] OR 
            r."observationTag" && %s::text[]
        """
        cursor.execute(query, (choiceDrink, choiceFlavour, preferences))
        results = cursor.fetchall()

        # Store results in a dictionary
        for listing in results:
            recommended[listing["id"]] = listing

    print("Recommended Listings:", list(recommended.values()))

    if not recommended:
        # return jsonify({"error": "No recommended listings found"}), 400
        return {}

    # return jsonify(list(recommended.values()))
    return recommended

# helper function for advanced algo (reviews)
def advanced_algo_reviews(userID):
    conn = g.db
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Fetch user's reviews
        cursor.execute('SELECT "flavourTag" FROM "reviews" WHERE "userID" = %s', (userID,))
        user_reviews_tags = cursor.fetchall()
        if not user_reviews_tags:
            return jsonify([])
        cursor.execute('''SELECT s1."id" as "id1", s2."id" as "id2" FROM "associations" a, "subTags" s1, "subTags" s2 
                        WHERE s1."subTag" = a."subTag1" AND s2."subTag" = a."subTag2"''')     
        associations = cursor.fetchall()
        tag1 = [assoc['id1'] for assoc in associations]
        tag2 = [assoc['id2'] for assoc in associations]
        associations_dict = {}
        for i in range(len(tag1)):
            if tag1[i] not in associations_dict:
                associations_dict[tag1[i]] = []
            associations_dict[tag1[i]].append(tag2[i])
            if tag2[i] not in associations_dict:
                associations_dict[tag2[i]] = []
            associations_dict[tag2[i]].append(tag1[i])
        # print(associations_dict)
        # return jsonify(associations_dict)
        tags_used = {}
        for tag in user_reviews_tags:
            for num in tag["flavourTag"]:
                if num not in tags_used:
                    tags_used[num] = 1
                else:
                    tags_used[num] += 1
        top_tags = sorted(tags_used, key=tags_used.get, reverse=True)[:5]
        print(top_tags)
        close_tags = []
        for tag in top_tags:
            if int(tag) in associations_dict:
                close_tags += associations_dict[int(tag)]
        close_tags = list(set(close_tags))
        print(close_tags)
        recommended = {}
        flavour_query = '''
            SELECT DISTINCT l.*
            FROM "listings" l
            JOIN "reviews" r ON l."id" = r."reviewTarget"
            WHERE r."flavourTag" && %s::text[]
        '''
        cursor.execute(flavour_query, (close_tags,))
        flavour_listings = cursor.fetchall()

        for listing in flavour_listings:
            if listing["id"] not in recommended:
                recommended[listing["id"]] = listing

        if not recommended:
            return {}
        return recommended
        
# helper function for advanced algo (drink lists) [TO DO]
# def advanced_algo_list(userID):

@blueprint.route("/getRecommendedListings/<userID>")
def getRecommendedListings(userID):
    print(userID)
    conn = g.db
    recommended = basic_algo(userID)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute('SELECT COUNT(*) from "reviews" where "userID" = %s', (userID,))
        review_count = cursor.fetchone()
        if review_count["count"] >= 5:
            advanced_algo_review_recc = advanced_algo_reviews(userID)
            recommended = {**recommended, **advanced_algo_review_recc}
    recommended = list(recommended.values())
    random.shuffle(recommended)
    return jsonify(recommended)

@blueprint.route("testRecommender/<userID>")
def testRecommender(userID):
    return advanced_algo_reviews(userID)       

# -----------------------------------------------------------------------------------------
# [GET] Specific Listing
@blueprint.route("/getListing/<id>")
def getListing(id):
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings" WHERE "id" = %s', (id,))
        listing_data = cursor.fetchone()

    if listing_data is None:
        return jsonify([])
    
    return jsonify(listing_data)

# -----------------------------------------------------------------------------------------
# [GET] Reverse Search Image Results, getting lsiting based on logo
@blueprint.route("/getListingsByLogo", methods=["POST"])
def get_listings_by_logo():
    data = request.json
    detected_logo = data.get("logo")

    if not detected_logo:
        return jsonify({"error": "No logo provided"}), 400

    conn = g.db  # Assuming you are using Flask's g for database connection
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        # Query producer using detected logo
        cursor.execute(
            'SELECT "id", "producerName" FROM "producers" WHERE LOWER(TRIM("producerName")) ILIKE %s LIMIT 1',
            (f"%{detected_logo.lower()}%",)
        )
        producer = cursor.fetchone()

        if not producer:
            return jsonify({"error": "No matching producer found"}), 404

        producer_id = producer["id"]
        producer_name = producer["producerName"]

        # Get listings by producer ID
        cursor.execute('SELECT * FROM "listings" WHERE "producerID" = %s LIMIT 30', (producer_id,))
        listings = cursor.fetchall()

        if not listings:
            return jsonify({"message": f"No listings found for {producer_name}"}), 404

        # Convert to a list of dictionaries
        listings_list = [dict(listing) for listing in listings]

    return jsonify(listings_list), 200

# [GET] Specific Listings By Producer
@blueprint.route("/getListingsByProducer/<id>")
def getListingsByProducer(id):
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings" WHERE "producerID" = %s', (id,))
        listings_data = cursor.fetchall()

    if not listings_data:
        return jsonify([])

    return jsonify(listings_data)

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# [GET] Producers
@blueprint.route("/getProducers")
def getProducers():
    conn = g.db
    cur = conn.cursor()

    try:
        # Query to get producers and related data
        query = """
            SELECT 
                p.id, p."producerName", p."producerDesc", p."originCountry", p."mainDrinks", p.photo, 
                p."hashedPassword", p."claimStatus", p."statusOB", p.username, p."producerLink", 
                p."stripeCustomerId", p."claimStatusCheckDate", p."isIndependentBottler",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId",
                        'producerId', qa."producerId"
                    ))
                    FROM "producersQuestionAnswers" qa
                    WHERE qa."producerId" = p.id
                ), '[]') AS "questionsAnswers",
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "producersOpeningHours" oh
                    WHERE oh."producerId" = p.id
                ), '{}'::json) AS "openingHours",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'producerId', u."producerId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "producerUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ) ORDER BY u.id)
                    FROM "producersUpdates" u
                    WHERE u."producerId" = p.id
                ), '[]') AS updates
            FROM producers p
            ORDER BY p.id
        """
        # query = """
        #     SELECT 
        #         p.id, p."producerName", p."producerDesc", p."originCountry", p."mainDrinks", p.photo, 
        #         p."hashedPassword", p."claimStatus", p."statusOB", p.username, p."producerLink", 
        #         p."stripeCustomerId", p."claimStatusCheckDate",
        #         COALESCE((
        #             SELECT json_agg(json_build_object(
        #                 'id', qa.id,
        #                 'question', qa.question,
        #                 'answer', qa.answer,
        #                 'date', qa.date,
        #                 'userId', qa."userId",
        #                 'producerId', qa."producerId"
        #             ))
        #             FROM "producersQuestionAnswers" qa
        #             WHERE qa."producerId" = p.id
        #         ), '[]') AS "questionsAnswers",
        #         COALESCE((
        #             SELECT json_agg(json_build_object(
        #                 'id', u.id,
        #                 'date', u.date,
        #                 'text', u.text,
        #                 'photo', u.photo,
        #                 'producerId', u."producerId",
        #                 'likes', COALESCE((
        #                     SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
        #                     FROM "producerUpdateLikes" l
        #                     WHERE l."updateId" = u.id
        #                 ), '[]')
        #             ) ORDER BY u.id)
        #             FROM "producersUpdates" u
        #             WHERE u."producerId" = p.id
        #         ), '[]') AS updates
        #     FROM producers p
        #     ORDER BY p.id
        # """

        cur.execute(query)
        producers_data = cur.fetchall()

        if not producers_data:
            return jsonify([])

        producers_list = []
        for row in producers_data:
            producer = dict(row)
            producer['questionsAnswers'] = producer['questionsAnswers'] if producer['questionsAnswers'] else []
            producer['updates'] = producer['updates'] if producer['updates'] else []
            producers_list.append(producer)

        return jsonify(producers_list), 200

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving producers."
            }
        ), 500

    finally:
        cur.close()

# [GET] Specific Producer
@blueprint.route("/getProducer/<int:id>")
def getProducer(id):
    conn = g.db
    cur = conn.cursor()

    try:
        # Query to get a specific producer and related data
        query = """
            SELECT 
                p.id, p."producerName", p."producerDesc", p."originCountry", p."mainDrinks", p.photo, 
                p."hashedPassword", p."claimStatus", p."statusOB", p.username, p."producerLink", 
                p."stripeCustomerId", p."claimStatusCheckDate", p."isIndependentBottler",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId",
                        'producerId', qa."producerId"
                    ))
                    FROM "producersQuestionAnswers" qa
                    WHERE qa."producerId" = p.id
                ), '[]') AS "questionsAnswers",
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "producersOpeningHours" oh
                    WHERE oh."producerId" = p.id
                ), '{}'::json) AS "openingHours",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'producerId', u."producerId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "producerUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ))
                    FROM "producersUpdates" u
                    WHERE u."producerId" = p.id
                ), '[]') AS updates
            FROM producers p
            WHERE p.id = %s
        """

        cur.execute(query, (id,))
        producer_data = cur.fetchone()

        if producer_data is None:
            return jsonify({"message": "Producer not found"}), 404

        producer = dict(producer_data)
        producer['questionsAnswers'] = producer['questionsAnswers'] if producer['questionsAnswers'] else []
        producer['updates'] = producer['updates'] if producer['updates'] else []

        return jsonify(producer), 200

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the producer."
            }
        ), 500

    finally:
        cur.close()


# [GET] Get recent listing reviews by a specific user + top 5 listings based on the review ratings + number of reviews done (aka drink count)
@blueprint.route("/getRecentListingReviews/<id>")
def getRecentListingReviews(id):

    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT "reviews".*, "reviewsUserVotes"."upvotes", "reviewsUserVotes"."downvotes"
            FROM "reviews"
            LEFT JOIN "reviewsUserVotes" ON "reviews"."id" = "reviewsUserVotes"."reviewId"
            WHERE "reviews"."userID" = %s 
            AND "reviews"."reviewType" = 'Listing'
            AND "reviews"."createdDate" >= NOW() - INTERVAL '5 days'
            ORDER BY "reviews"."createdDate" DESC
            LIMIT 10
        """, (id,))

        reviews_data = cursor.fetchall()

        if not reviews_data:
            reviews_data = []

    for review in reviews_data:
        review["userVotes"] = {
            "upvotes": review["upvotes"] if review["upvotes"] else [],
            "downvotes": review["downvotes"] if review["downvotes"] else []
        }
        del review["upvotes"]
        del review["downvotes"]

    # Retrieve top 5 listings based on the review ratings
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT "reviewTarget" FROM "reviews" WHERE "reviewType" = 'Listing' AND "rating" >= 8
            LIMIT 10
        """)
        top_listings_data = cursor.fetchall()

    top_listings = []

    # Convert the top listings data to a list
    for listing in top_listings_data:
        top_listings.append(listing["reviewTarget"])

    # Retrieve the number of reviews done by the user (number of unique listings reviewed)
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(DISTINCT "reviewTarget") FROM "reviews" WHERE "userID" = %s', (id,))
        drink_count = cursor.fetchone()


    return jsonify({"recentReview" : reviews_data,
                    "topListings" : top_listings,
                    "drinkCount" : drink_count["count"]}), 200
    

# [GET] Get all listings names
@blueprint.route("/getAllListingsNames")
def getAllListingsNames():
    conn = g.db
    with conn.cursor() as cursor:
        cursor.execute('SELECT "id", "listingName" FROM "listings"')
        listings_data = cursor.fetchall()

    if not listings_data:
        return jsonify([]), 404

    return jsonify(listings_data), 200

# [POST] Get bookmarked listings
@blueprint.route("/getBookmarkListings", methods=['POST'])
def getBookmarkListings():
    conn = g.db
    listing_ids = [listing["drinkId"] for listing in request.json.get('listingIDs', [])]

    if not listing_ids:
        return jsonify({
            "code": 404,
            "message": "At least one listing ID is required."
        }), 404

    # Retrieve listing information based on the provided IDs
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "listings" WHERE "id" IN %s', (tuple(listing_ids),))
        bookmarked_listings = cursor.fetchall()

        if not bookmarked_listings:
            return jsonify([]), 404

        return_data = {}
        # Fetch the average review rating for each listing
        for listing in bookmarked_listings:
            cursor.execute('SELECT AVG("rating") FROM "reviews" WHERE "reviewTarget" = %s', (listing["id"],))
            avg_rating = cursor.fetchone()

            # Add to listing data
            return_data[listing["id"]] = listing
            return_data[listing["id"]]["avgRating"] = avg_rating["avg"]

    return jsonify(return_data), 200

# [GET] Get user's review summary
@blueprint.route("/getUserReviewSummary/<id>")
def getUserReviewSummary(id):
    conn = g.db

    with conn.cursor() as cursor:
        # Step 1: Get all listings reviewed by the user
        cursor.execute('''
            SELECT "reviewTarget", "address", "taggedUsers"
            FROM "reviews"
            WHERE "userID" = %s
        ''', (id,))
        reviewed_listings = cursor.fetchall()

        if not reviewed_listings:
            return jsonify({
                "code": 404,
                "message": "No reviews found for the specified user."
            }), 404
        
        # Use a set for distinct reviewTargets and addresses, but allow duplicates for taggedUsers
        unique_listing_id = []
        locations_tagged = set()
        tagged_users = []

        for review in reviewed_listings:
            # Add distinct reviewTargets
            if review.get("reviewTarget"):
                if review["reviewTarget"] not in unique_listing_id:
                    unique_listing_id.append(review["reviewTarget"])
            # Add distinct addresses
            if review.get("address"):
                locations_tagged.add(review["address"])
            # For taggedUsers, append all users (assuming it's stored as an array)
            if review.get("taggedUsers"):
                tagged_users.extend(review["taggedUsers"])

        locations_tagged = list(locations_tagged)
        tagged_users_count = len(tagged_users)

        # Step 2: Get the number of unique drinkType and typeCategory based on the listings reviewed
        categories_reviewed_dict = {}  # {drinkType: {typeCategory: count, ...}, ...}
        for listing_id in unique_listing_id:
            cursor.execute('SELECT "drinkType", "typeCategory" FROM "listings" WHERE "id" = %s', (listing_id,))
            drink_data = cursor.fetchone()
            if drink_data:
                drink_type = drink_data["drinkType"]
                drink_category = drink_data["typeCategory"]

                if drink_type not in categories_reviewed_dict:
                    categories_reviewed_dict[drink_type] = {}

                # Increment the count for the drink_category within the given drink_type.
                if drink_category in categories_reviewed_dict[drink_type]:
                    categories_reviewed_dict[drink_type][drink_category] += 1
                else:
                    categories_reviewed_dict[drink_type][drink_category] = 1

        # Step 3: Get the number of upvotes for the user's reviews (new schema)
        cursor.execute('''
            SELECT COUNT(*) FROM "reviewsUserVotes"
            WHERE EXISTS (
                SELECT 1 FROM jsonb_array_elements("upvotes") AS upvote
                WHERE (upvote->>'userId')::TEXT = %s
            )
        ''', (id,))
        upvotes_count = cursor.fetchone()['count']

    return jsonify({
        "code": 200,
        "message": "User review summary fetched successfully.",
        "data": {
            "categoriesReviewed": categories_reviewed_dict,
            "locationsTagged": locations_tagged,
            "upvotesCount": upvotes_count,
            "taggedUsers": tagged_users_count
        }
    })


# [GET] Specific Producer
@blueprint.route("/getProducerByRequestId/<id>")
def getProducerByRequestId(id):
    conn = g.db
    cur = conn.cursor()

    try:
        query = """
            SELECT 
                p.id, p."producerName", p."producerDesc", p."originCountry", p."mainDrinks", p.photo, 
                p."hashedPassword", p."claimStatus", p."statusOB", p.username, p."producerLink", 
                p."stripeCustomerId", p."claimStatusCheckDate", p."isIndependentBottler",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId",
                        'producerId', qa."producerId"
                    ))
                    FROM "producersQuestionAnswers" qa
                    WHERE qa."producerId" = p.id
                ), '[]') AS "questionsAnswers",
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "producersOpeningHours" oh
                    WHERE oh."producerId" = p.id
                ), '{}'::json) AS "openingHours",
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'producerId', u."producerId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "producerUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ))
                    FROM "producersUpdates" u
                    WHERE u."producerId" = p.id
                ), '[]') AS updates
            FROM "producers" p
            WHERE p.id = %s
        """

        cur.execute(query, (id,))
        producer_data = cur.fetchone()

        if producer_data is None:
            return jsonify({"message": "Producer not found"}), 404

        producer = dict(producer_data)
        producer['questionsAnswers'] = producer['questionsAnswers'] if producer['questionsAnswers'] else []
        producer['updates'] = producer['updates'] if producer['updates'] else []

        return jsonify(producer), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the producer."
            }
        ), 500
    
    finally:
        cur.close()

# [GET] List of unique producers names and id
@blueprint.route("/getUniqueProducersNamesID")
def getUniqueProducersNamesID():
    conn = g.db
    with conn.cursor() as cursor:
        cursor.execute('SELECT DISTINCT "producerName", "isIndependentBottler", "id" FROM "producers"')
        producers_data = cursor.fetchall()

    if not producers_data:
        return jsonify({
            "code": 404,
            "message": "No producers found."
        })
    
    # Convert the data to a list of dictionaries

    producers_list = []
    for producer in producers_data:
        if producer["producerName"] == None:
            continue
        producer_dict = {
            "producerName": producer["producerName"],
            "isIndependentBottler": producer["isIndependentBottler"],
            "id": producer["id"]
        }
        producers_list.append(producer_dict)

    return jsonify({
        "code": 200,
        "message": "Producers fetched successfully.",
        "data": producers_list
    })




# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] Producers
# @blueprint.route("/getProducers")
# def getProducers():
#     db = g.db
#     # Fetch all producers
#     producers_data = db.producers.find({})
#     allProducers = []
#     for producer in producers_data:
#         # Fetch the related question answers based on the id stored in producer's questionAnswers
#         question_answers_data = db.producersQuestionAnswers.find({
#             "id": {"$in": producer['questionAnswers']}
#         })
#         producer['questionsAnswers'] = list(question_answers_data)
#         # Fetch the related updates based on the id stored in producer's updates
#         updates_data = db.producersUpdates.find({
#             "id": {"$in": producer['updates']}
#         })
#         producer['updates'] = list(updates_data)
#         allProducers.append(producer)
#     return parse_json(allProducers)

# # [GET] Specific Producer by ID
# @blueprint.route("/getProducer/<id>")
# def getProducer(id):
#     db = g.db
#     # Fetch the specific producer
#     producer = db.producers.find_one({"_id": ObjectId(id)})
#     if producer is None:
#         return []
#     # Fetch related question answers based on the id(s) in producer's questionAnswers
#     question_answers_data = db.producersQuestionAnswers.find({
#         "id": {"$in": producer['questionAnswers']}
#     })
#     producer['questionsAnswers'] = list(question_answers_data)
#     # Fetch related updates based on the id(s) in producer's updates
#     updates_data = db.producersUpdates.find({
#         "id": {"$in": producer['updates']}
#     })
#     producer['updates'] = list(updates_data)
#     return parse_json(producer)

# # [GET] Specific Producer by Request ID
# @blueprint.route("/getProducerByRequestId/<id>")
# def getProducerByRequestId(id):
#     db = g.db
#     # Fetch the specific producer by requestId
#     producer = db.producers.find_one({"requestId": ObjectId(id)})
#     if producer is None:
#         return []
#     # Fetch related question answers based on the id(s) in producer's questionAnswers
#     question_answers_data = db.producersQuestionAnswers.find({
#         "id": {"$in": producer['questionAnswers']}
#     })
#     producer['questionsAnswers'] = list(question_answers_data)
#     # Fetch related updates based on the id(s) in producer's updates
#     updates_data = db.producersUpdates.find({
#         "id": {"$in": producer['updates']}
#     })
#     producer['updates'] = list(updates_data)
#     return parse_json(producer)

# =======================================================

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# -- ========= [NEW!] "reviewsUserVotes" =========
# CREATE TABLE "reviewsUserVotes" (
#     "id" SERIAL PRIMARY KEY,
#     "upvotes" TEXT[], -- Contain "users"("id")s
#     "downvotes" TEXT[], -- Contain "users"("id")s
#     "reviewId" INTEGER REFERENCES "reviews"("id") on DELETE SET NULL -- [!] reference "reviews" FK
# );

# [GET] Reviews
@blueprint.route("/getReviews")
def getReviews():
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT "reviews".*, "reviewsUserVotes"."upvotes", "reviewsUserVotes"."downvotes"
            FROM "reviews"
            LEFT JOIN "reviewsUserVotes" ON "reviews"."id" = "reviewsUserVotes"."reviewId"
        """)

        reviews_data = cursor.fetchall()
    
    if not reviews_data:
        return jsonify([])

    for review in reviews_data:
        review["userVotes"] = {
            "upvotes": review["upvotes"] if review["upvotes"] else [],
            "downvotes": review["downvotes"] if review["downvotes"] else []
        }
        del review["upvotes"]
        del review["downvotes"]

    return jsonify(reviews_data)

# [GET] Specific Reviews by reviewTarget
@blueprint.route("/getReviewByTarget/<id>")
def getReviewByTarget(id):
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "reviews" WHERE "reviewTarget" = %s', (id,))
        reviews_data = cursor.fetchall()
    
    if not reviews_data:
        return jsonify([])

    return jsonify(reviews_data)


# [GET] Latest 10 Specific Reviews by usr(s) - using one or more user IDs (retrieve latest reviews for the specified user(s) as well as the review target(s) data)
@blueprint.route("/getReviewsByUserIds")
def getReviewsByUserIds():

    user_ids_str = request.args.get('user_ids')
    user_ids = user_ids_str.split(',')
    conn = g.db
    
    with conn.cursor() as cursor:
        # Fetch latest reviews for the specified user(s)
        cursor.execute('''
            WITH latest_reviews AS (
                SELECT "reviewDesc", "rating", "reviewTarget", "createdDate", "userID"
                FROM "reviews"
                WHERE "userID" IN %s
                ORDER BY "createdDate" DESC
                LIMIT 10
            )
            SELECT "reviewDesc", "rating", "reviewTarget", "createdDate", "userID"
            FROM latest_reviews
            ORDER BY "createdDate" DESC;
        ''', (tuple(user_ids),))
        latest_reviews = cursor.fetchall()

        # Retrieve the display name(s) for each user
        cursor.execute('SELECT "id", "displayName", "photo" FROM "users" WHERE "id" IN %s', (tuple(user_ids),))
        user_display_names = cursor.fetchall()

        # Convert the user display names to dictionary format where the key is the user ID
        user_display_names = {user['id']: user for user in user_display_names}

        # Retrieve the review target(s) for each review
        review_target_list = []
        for review in latest_reviews:
            review = dict(review)
            if (review['reviewTarget'] not in review_target_list):
                review_target_list.append(review['reviewTarget'])
        
        # Fetch the review target(s) data
        cursor.execute('SELECT "id", "listingName", "photo" FROM "listings" WHERE "id" IN %s', (tuple(review_target_list),))
        review_targets_data = cursor.fetchall()

        # Map the review target data to the reviews
        for review in latest_reviews:
            review['userInfo'] = user_display_names[review['userID']]
            review['reviewTarget'] = next((item for item in review_targets_data if item["id"] == review['reviewTarget']), None)
        
        # Convert the reviews to JSON format
        latest_reviews = parse_json(latest_reviews)
    
    if not latest_reviews:
        return jsonify({
            'code': 404,
            'message': 'No reviews found for the specified user(s).'
        })

    return jsonify({
        'code': 200,
        'message': 'Latest reviews fetched successfully.',
        'data': latest_reviews
    })

# [GET] Producer Tour Reviews
@blueprint.route("/getProducerTourReviews")
def getTourReviews():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT "producerReviews".*, "producerReviewsUserVotes"."upvotes", "producerReviewsUserVotes"."downvotes"
            FROM "producerReviews"
            LEFT JOIN "producerReviewsUserVotes" ON "producerReviews"."id" = "producerReviewsUserVotes"."reviewId"
        """)

        reviews_data = cursor.fetchall()

        if not reviews_data:
            return jsonify([])
        
        for review in reviews_data:
            review["userVotes"] = {
                "upvotes": review["upvotes"] if review["upvotes"] else [],
                "downvotes": review["downvotes"] if review["downvotes"] else []
            }
            del review["upvotes"]
            del review["downvotes"]

        return jsonify(reviews_data)

# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] Reviews
# @blueprint.route("/getReviews")
# def getReviews():
#     db = g.db
#     reviews_data = db.reviews.find({})
#     allReviews = []
#     for review in reviews_data:
#         # Fetch related user votes based on the id(s) in review's userVotes
#         user_votes_data = db.reviewsUserVotes.find({
#             "_id": {"$in": review['userVotes']}
#         })
#         review['userVotes'] = list(user_votes_data)
#         allReviews.append(review)
#     return parse_json(allReviews)

# # [GET] Specific Reviews by reviewTarget
# @blueprint.route("/getReviewByTarget/<id>")
# def getReviewByTarget(id):
#     db = g.db
#     reviews_data = db.reviews.find({"reviewTarget": ObjectId(id)})
#     if reviews_data is None:
#         return []
#     allReviews = []
#     for review in reviews_data:
#         # Fetch related user votes based on the id(s) in review's userVotes
#         user_votes_data = db.reviewsUserVotes.find({
#             "_id": {"$in": review['userVotes']}
#         })
#         review['userVotes'] = list(user_votes_data)
#         allReviews.append(review)
#     return parse_json(allReviews)

# =======================================================

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# [GET] Users
@blueprint.route("/getUsers")
def getUsers():
    conn = g.db
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM "users"')
            users_data = cursor.fetchall()

            for user_data in users_data:
                user_id = user_data['id']
                
                user_data["drinkLists"] = fetch_drink_lists(cursor, user_id)
                user_data["followLists"] = fetch_follow_lists(cursor, user_id)

        return jsonify(users_data), 200

    except Exception as e:
        print(str(e))
        return jsonify({"code": 500, "message": "An error occurred while fetching users."}), 500

# [GET] Specific User by ID
@blueprint.route("/getUser/<id>")
def getUser(id):
    print("Getting user with id: ", id)
    conn = g.db
    
    try:
        with conn.cursor() as cursor:
            user_data = fetch_user_data(cursor, id)
            if not user_data:
                return jsonify({}), 404

            user_data["drinkLists"] = fetch_drink_lists(cursor, id)
            user_data["followLists"] = fetch_follow_lists(cursor, id)

        return jsonify(user_data), 200

    except Exception as e:
        print(str(e))
        return jsonify({"code": 500, "message": "An error occurred while fetching the user."}), 500


# [GET] Get user profile photo by ID
@blueprint.route("/getUserPhoto/<id>/<userType>")
def getUserPhoto(id, userType):

    conn = g.db
    try:
        with conn.cursor() as cursor:
            if userType == "producer":
                cursor.execute('SELECT "photo" FROM "producers" WHERE "id" = %s', (id,))
            elif userType == "venue":
                cursor.execute('SELECT "photo" FROM "venues" WHERE "id" = %s', (id,))
            else:
                cursor.execute('SELECT "photo" FROM "users" WHERE "id" = %s', (id,))
            photo = cursor.fetchone()
        
        if not photo:
            return jsonify([]), 404
        
        # Standardize the photo field
        if photo["photo"] == None:
            photo["photo"] = ""

        return jsonify(photo), 200

    except Exception as e:
        print(str(e))
        return jsonify({"code": 500, "message": "An error occurred while fetching the user photo."}), 500



# [GET] Specific User by Username
@blueprint.route("/getUserByUsername/<username>")
def getUserByUsername(username):
    conn = g.db
    
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM "users" WHERE "username" = %s', (username,))
            user_data = cursor.fetchone()
        
            if not user_data:
                return jsonify([]), 404

            user_id = user_data['id']

            user_data["drinkLists"] = fetch_drink_lists(cursor, user_id)
            user_data["followLists"] = fetch_follow_lists(cursor, user_id)

        return jsonify(user_data), 200

    except Exception as e:
        print(str(e))
        return jsonify({"code": 500, "message": "An error occurred while fetching the user."}), 500

# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] Users
# @blueprint.route("/getUsers")
# def getUsers():
#     db = g.db
#     users_data = db.users.find({})
#     allUsers = []
#     for user in users_data:
#         # Fetch related drink lists based on the id(s) in user's drinkLists
#         drink_lists_data = db.usersDrinkLists.find({
#             "_id": {"$in": user['drinkLists']}
#         })
#         user['drinkLists'] = list(drink_lists_data)
#         # Fetch related follow lists based on the id(s) in user's followLists
#         follow_lists_data = db.usersFollowLists.find({
#             "_id": {"$in": user['followLists']}
#         })
#         user['followLists'] = list(follow_lists_data)
#         allUsers.append(user)
#     return parse_json(allUsers)

# # [GET] Specific User by ID
# @blueprint.route("/getUser/<id>")
# def getUser(id):
#     db = g.db
#     user = db.users.find_one({"_id": ObjectId(id)})
#     if user is None:
#         return []
#     # Fetch related drink lists based on the id(s) in user's drinkLists
#     drink_lists_data = db.usersDrinkLists.find({
#         "_id": {"$in": user['drinkLists']}
#     })
#     user['drinkLists'] = list(drink_lists_data)
#     # Fetch related follow lists based on the id(s) in user's followLists
#     follow_lists_data = db.usersFollowLists.find({
#         "_id": {"$in": user['followLists']}
#     })
#     user['followLists'] = list(follow_lists_data)
#     return parse_json(user)

# # [GET] Specific User by Username
# @blueprint.route("/getUserByUsername/<username>")
# def getUserByUsername(username):
#     db = g.db
#     user = db.users.find_one({"username": username})
#     if user is None:
#         return []
#     # Fetch related drink lists based on the id(s) in user's drinkLists
#     drink_lists_data = db.usersDrinkLists.find({
#         "_id": {"$in": user['drinkLists']}
#     })
#     user['drinkLists'] = list(drink_lists_data)
#     # Fetch related follow lists based on the id(s) in user's followLists
#     follow_lists_data = db.usersFollowLists.find({
#         "_id": {"$in": user['followLists']}
#     })
#     user['followLists'] = list(follow_lists_data)
#     return parse_json(user)

# =======================================================

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# [GET] Venues
@blueprint.route("/getVenues")
def getVenues():
    conn = g.db
    cur = conn.cursor()

    try:
        # Query to get venues and related data
        query = """
            SELECT 
                v.id, v.address, v."claimStatus", v."hashedPassword", v."venueName", v."venueDesc", 
                v."originLocation", v.photo, v."publicHolidays", v."reservationDetails", v."claimStatusCheckDate",
                v.username, v."venueType", v."stripeCustomerId", v.pin,
                -- Build the menu JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'sectionOrder',vm."sectionOrder",
                        'sectionName', vm."sectionName",
                        'sectionId', vm.id,
                        'sectionMenu', COALESCE((
                            SELECT json_agg(json_build_object(
                                'itemOrder', mi."itemOrder",
                                'itemPrice', mi."itemPrice",
                                'itemAvailability', mi."itemAvailability",
                                'itemID', mi."itemID",
                                'itemServingType', mi."itemServingType"
                            ) ORDER BY mi."itemOrder")
                            FROM "menuItems" mi
                            WHERE mi."sectionId" = vm.id
                        ), '[]')
                    ) ORDER BY vm."sectionOrder")
                    FROM "venuesMenu" vm
                    WHERE vm."venueId" = v.id
                ), '[]') AS menu,
                -- Build openingHours JSON
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "venuesOpeningHours" oh
                    WHERE oh."venueId" = v.id
                ), '{}'::json) AS "openingHours",
                -- Build questionsAnswers JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId"
                    ))
                    FROM "venuesQuestionAnswers" qa
                    WHERE qa."venueId" = v.id
                ), '[]') AS "questionsAnswers",
                -- Build updates JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'venueId', u."venueId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "venueUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ) ORDER BY u.date DESC)
                    FROM "venuesUpdates" u
                    WHERE u."venueId" = v.id
                ), '[]') AS updates
            FROM venues v
            ORDER BY v.id
        """

        cur.execute(query)
        venues_data = cur.fetchall()

        if not venues_data:
            return jsonify([])

        venues_list = []
        for row in venues_data:
            venue = dict(row)
            venue['menu'] = venue['menu'] if venue['menu'] else []
            venue['openingHours'] = venue['openingHours'] if venue['openingHours'] else {}
            venue['questionsAnswers'] = venue['questionsAnswers'] if venue['questionsAnswers'] else []
            venue['updates'] = venue['updates'] if venue['updates'] else []
            venues_list.append(venue)

        return jsonify(venues_list), 200

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving venues."
            }
        ), 500

    finally:
        cur.close()

# [GET] Specific Venue
@blueprint.route("/getVenue/<id>")
def getVenue(id):
    conn = g.db
    cur = conn.cursor()

    try:
        # Query to get a specific venue and related data
        query = """
            SELECT 
                v.id, v.address, v."claimStatus", v."hashedPassword", v."venueName", v."venueDesc", 
                v."originLocation", v.photo, v."publicHolidays", v."reservationDetails", v."claimStatusCheckDate",
                v.username, v."venueType", v."stripeCustomerId", v.pin,
                -- Build the menu JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'sectionOrder', vm."sectionOrder",
                        'sectionName', vm."sectionName",
                        'sectionId', vm.id,
                        'sectionMenu', COALESCE((
                            SELECT json_agg(json_build_object(
                                'itemOrder', mi."itemOrder",
                                'itemPrice', mi."itemPrice",
                                'itemAvailability', mi."itemAvailability",
                                'itemID', mi."itemID",
                                'itemServingType', mi."itemServingType"
                            ) ORDER BY mi."itemOrder")
                            FROM "menuItems" mi
                            WHERE mi."sectionId" = vm.id
                        ), '[]')
                    ) ORDER BY vm."sectionOrder")
                    FROM "venuesMenu" vm
                    WHERE vm."venueId" = v.id
                ), '[]') AS menu,
                -- Build openingHours JSON
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "venuesOpeningHours" oh
                    WHERE oh."venueId" = v.id
                ), '{}'::json) AS "openingHours",
                -- Build questionsAnswers JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId"
                    ))
                    FROM "venuesQuestionAnswers" qa
                    WHERE qa."venueId" = v.id
                ), '[]') AS "questionsAnswers",
                -- Build updates JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'venueId', u."venueId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "venueUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ) ORDER BY u.date DESC)
                    FROM "venuesUpdates" u
                    WHERE u."venueId" = v.id
                ), '[]') AS updates
            FROM venues v
            WHERE v.id = %s
            GROUP BY v.id
        """

        cur.execute(query, (id,))
        venue_data = cur.fetchone()

        if venue_data is None:
            return jsonify({"message": "Venue not found"}), 404

        venue = dict(venue_data)
        venue['menu'] = venue['menu'] if venue['menu'] else []
        venue['openingHours'] = venue['openingHours'] if venue['openingHours'] else {}
        venue['questionsAnswers'] = venue['questionsAnswers'] if venue['questionsAnswers'] else []
        venue['updates'] = venue['updates'] if venue['updates'] else []

        return jsonify(venue), 200

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the venue."
            }
        ), 500

    finally:
        cur.close()

# [GET] Specific Producer
@blueprint.route("/getVenueByRequestId/<id>")
def getVenueByRequestId(id):
    conn = g.db
    cur = conn.cursor()

    try:
        # Query to get a specific venue by requestId and related data
        query = """
            SELECT 
                v.id, v.address, v."claimStatus", v."hashedPassword", v."venueName", v."venueDesc", 
                v."originLocation", v.photo, v."publicHolidays", v."reservationDetails", v."claimStatusCheckDate",
                v.username, v."venueType", v."stripeCustomerId", v.pin,
                -- Build the menu JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'sectionOrder', vm."sectionOrder",
                        'sectionName', vm."sectionName",
                        'sectionId', vm.id,
                        'sectionMenu', COALESCE((
                            SELECT json_agg(json_build_object(
                                'itemOrder', mi."itemOrder",
                                'itemPrice', mi."itemPrice",
                                'itemAvailability', mi."itemAvailability",
                                'itemID', mi."itemID",
                                'itemServingType', mi."itemServingType"
                            ) ORDER BY mi."itemOrder")
                            FROM "menuItems" mi
                            WHERE mi."sectionId" = vm.id
                        ), '[]')
                    ) ORDER BY vm."sectionOrder")
                    FROM "venuesMenu" vm
                    WHERE vm."venueId" = v.id
                ), '[]') AS menu,
                -- Build openingHours JSON
                COALESCE((
                    SELECT row_to_json(oh)
                    FROM "venuesOpeningHours" oh
                    WHERE oh."venueId" = v.id
                ), '{}'::json) AS "openingHours",
                -- Build questionsAnswers JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', qa.id,
                        'question', qa.question,
                        'answer', qa.answer,
                        'date', qa.date,
                        'userId', qa."userId"
                    ))
                    FROM "venuesQuestionAnswers" qa
                    WHERE qa."venueId" = v.id
                ), '[]') AS "questionsAnswers",
                -- Build updates JSON
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id', u.id,
                        'date', u.date,
                        'text', u.text,
                        'photo', u.photo,
                        'venueId', u."venueId",
                        'likes', COALESCE((
                            SELECT json_agg(json_build_object('userId', l."userId", 'userType', l."userType"))
                            FROM "venueUpdateLikes" l
                            WHERE l."updateId" = u.id
                        ), '[]')
                    ) ORDER BY u.date DESC)
                    FROM "venuesUpdates" u
                    WHERE u."venueId" = v.id
                ), '[]') AS updates
            FROM venues v
            WHERE v.id = %s
            GROUP BY v.id
        """

        cur.execute(query, (id,))
        venue_data = cur.fetchone()

        if venue_data is None:
            return jsonify({"message": "Venue not found"}), 404

        venue = dict(venue_data)
        venue['menu'] = venue['menu'] if venue['menu'] else []
        venue['openingHours'] = venue['openingHours'] if venue['openingHours'] else {}
        venue['questionsAnswers'] = venue['questionsAnswers'] if venue['questionsAnswers'] else []
        venue['updates'] = venue['updates'] if venue['updates'] else []

        return jsonify(venue), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the venue."
            }
        ), 500
    
    finally:
        cur.close()

# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] Venues
# @blueprint.route("/getVenues")
# def getVenues():
#     db = g.db
#     venues_data = db.venues.find({})
#     allVenues = []
#     for venue in venues_data:
#         # Fetch related menu based on the id(s) in venue's menu
#         menu_data = db.venuesMenu.find({
#             "_id": {"$in": venue['menu']}
#         })
#         venue['menu'] = list(menu_data)
#         # Fetch related opening hours based on the id(s) in venue's openingHours
#         opening_hours_data = db.venuesOpeningHours.find({
#             "_id": {"$in": venue['openingHours']}
#         })
#         venue['openingHours'] = list(opening_hours_data)
#         # Fetch related question answers based on the id(s) in venue's questionAnswers
#         question_answers_data = db.venuesQuestionAnswers.find({
#             "_id": {"$in": venue['questionAnswers']}
#         })
#         venue['questionAnswers'] = list(question_answers_data)
#         # Fetch related updates based on the id(s) in venue's updates
#         updates_data = db.venuesUpdates.find({
#             "_id": {"$in": venue['updates']}
#         })
#         venue['updates'] = list(updates_data)
#         allVenues.append(venue)
#     return parse_json(allVenues)

# # [GET] Specific Venue by ID
# @blueprint.route("/getVenue/<id>")
# def getVenue(id):
#     db = g.db
#     venue = db.venues.find_one({"_id": ObjectId(id)})
#     if venue is None:
#         return []
#     # Fetch related menu based on the id(s) in venue's menu
#     menu_data = db.venuesMenu.find({
#         "_id": {"$in": venue['menu']}
#     })
#     venue['menu'] = list(menu_data)
#     # Fetch related opening hours based on the id(s) in venue's openingHours
#     opening_hours_data = db.venuesOpeningHours.find({
#         "_id": {"$in": venue['openingHours']}
#     })
#     venue['openingHours'] = list(opening_hours_data)
#     # Fetch related question answers based on the id(s) in venue's questionAnswers
#     question_answers_data = db.venuesQuestionAnswers.find({
#         "_id": {"$in": venue['questionAnswers']}
#     })
#     venue['questionAnswers'] = list(question_answers_data)
#     # Fetch related updates based on the id(s) in venue's updates
#     updates_data = db.venuesUpdates.find({
#         "_id": {"$in": venue['updates']}
#     })
#     venue['updates'] = list(updates_data)
#     return parse_json(venue)

# # [GET] Specific Venue by Request ID
# @blueprint.route("/getVenueByRequestId/<id>")
# def getVenueByRequestId(id):
#     db = g.db
#     venue = db.venues.find_one({"requestId": ObjectId(id)})
#     if venue is None:
#         return []
#     # Fetch related menu based on the id(s) in venue's menu
#     menu_data = db.venuesMenu.find({
#         "_id": {"$in": venue['menu']}
#     })
#     venue['menu'] = list(menu_data)
#     # Fetch related opening hours based on the id(s) in venue's openingHours
#     opening_hours_data = db.venuesOpeningHours.find({
#         "_id": {"$in": venue['openingHours']}
#     })
#     venue['openingHours'] = list(opening_hours_data)
#     # Fetch related question answers based on the id(s) in venue's questionAnswers
#     question_answers_data = db.venuesQuestionAnswers.find({
#         "_id": {"$in": venue['questionAnswers']}
#     })
#     venue['questionAnswers'] = list(question_answers_data)
#     # Fetch related updates based on the id(s) in venue's updates
#     updates_data = db.venuesUpdates.find({
#         "_id": {"$in": venue['updates']}
#     })
#     venue['updates'] = list(updates_data)
#     return parse_json(venue)

# =======================================================

# -----------------------------------------------------------------------------------------
# [GET] VenuesAPI
# @blueprint.route("/getVenuesAPI")
# def getVenuesAPI():
#     db = g.db
#     data = db.venuesAPI.find({})
#     print(len(list(data.clone())))
#     allVenuesAPI = []
#     dataEncode = parse_json(data)
#     for doc in dataEncode:
#         allVenuesAPI.append(doc)
#     return allVenuesAPI

# -----------------------------------------------------------------------------------------
# [GET] DrinkTypes
@blueprint.route("/getDrinkTypes")
def getDrinkTypes():
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "drinkTypes"')
        drink_types_data = cursor.fetchall()
    
    if not drink_types_data:
        return jsonify([])

    return jsonify(drink_types_data)

# -----------------------------------------------------------------------------------------
# [GET] RequestListings
@blueprint.route("/getRequestListings")
def getRequestListings():
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "requestListings"')
        request_listings_data = cursor.fetchall()
    
    if not request_listings_data:
        return jsonify([])

    return jsonify(request_listings_data)

# [GET] Specific Request Listing
@blueprint.route("/getRequestListing/<id>")
def getRequestListing(id):
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "requestListings" WHERE "id" = %s', (id,))
        request_listing_data = cursor.fetchone()
    
    if request_listing_data is None:
        return jsonify([])

    return jsonify(request_listing_data)

# -----------------------------------------------------------------------------------------
# [GET] RequestEdits
@blueprint.route("/getRequestEdits")
def getRequestEdits():
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "requestEdits"')
        request_edits_data = cursor.fetchall()
    
    if not request_edits_data:
        return jsonify([])

    return jsonify(request_edits_data)

# [GET] Specific Request Edit
@blueprint.route("/getRequestEdit/<id>")
def getRequestEdit(id):
    conn = g.db
    
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "requestEdits" WHERE "id" = %s', (id,))
        request_edit_data = cursor.fetchone()
    
    if request_edit_data is None:
        return jsonify([])

    return jsonify(request_edit_data)

# -----------------------------------------------------------------------------------------
# [GET] modRequests
@blueprint.route("/getModRequests")
def getModRequests():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "modRequests"')
        mod_requests_data = cursor.fetchall()

    if not mod_requests_data:
        return jsonify([])

    return jsonify(mod_requests_data)

# -----------------------------------------------------------------------------------------
# [GET] flavourTags
@blueprint.route("/getFlavourTags")
def getFlavourTags():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "flavourTags"')
        flavour_tags_data = cursor.fetchall()

    if not flavour_tags_data:
        return jsonify([])

    return jsonify(flavour_tags_data)
# -----------------------------------------------------------------------------------------
# [GET] subTags
@blueprint.route("/getSubTags")
def getSubTags():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "subTags"')
        allSubTags = cursor.fetchall()

    if not allSubTags:
        return jsonify([])

    return jsonify(allSubTags)

# -----------------------------------------------------------------------------------------
# [GET] observationTags
@blueprint.route("/getObservationTags")
def getObservationTags():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "observationTags"')
        observation_tags_data = cursor.fetchall()

    if not observation_tags_data:
        return jsonify([])

    return jsonify(observation_tags_data)

@blueprint.route("/getListingsByObservationTag/<tag>")
def get_listings_by_observation_tag(tag):
    selected_tag = tag  

    if not selected_tag:
        return jsonify({"error": "Tag is required"}), 400

    conn = g.db  

    try:
        with conn.cursor() as cursor:
            query = """
            SELECT DISTINCT l.*
            FROM "listings" l
            JOIN "reviews" r ON l."id" = r."reviewTarget"
            WHERE %s = ANY(r."observationTag");
            """
            cursor.execute(query, (selected_tag,))

            listings = cursor.fetchall()  # Fetch results as dictionaries

            # Convert the dictionary rows into a list of dictionaries
            listing_dicts = [dict(row) for row in listings]

            # Debugging output
            print("Listings as Dicts:", listing_dicts)

        # Return the result as JSON
        return jsonify(listing_dicts)

    except Exception as e:
        # If an error occurs, print the error message and return an error response
        print(f"Error fetching listings: {e}")
        return jsonify({"error": "A server error occurred."}), 500

# -----------------------------------------------------------------------------------------
# [GET] Top 8 Trending Observation Tags
@blueprint.route("/getTop8")
def getTop8():
    conn = g.db

    with conn.cursor() as cursor:
        query = """
            SELECT TRIM(BOTH '"' FROM tag_name_clean) AS tag_name, SUM(tag_count) AS tag_count
            FROM (
                SELECT unnest(string_to_array(tag_name, ',')) AS tag_name_clean, tag_count
                FROM (
                    SELECT trim(both '"' FROM unnest(string_to_array(
                        replace(trim(both '{}' FROM "observationTag"::TEXT), '","', '|||'), '|||'
                    ))) AS tag_name, 1 AS tag_count
                    FROM "reviews"
                    WHERE "observationTag" IS NOT NULL
                ) sub
            ) final_sub
            GROUP BY TRIM(BOTH '"' FROM tag_name_clean)
            ORDER BY tag_count DESC
            LIMIT 8;
        """
        cursor.execute(query)
        top8_data = cursor.fetchall() 
        columns = [desc[0] for desc in cursor.description]  

        print("Columns:", columns)  
        print("Listings:", top8_data)  

        listing_dicts = []
        for row in top8_data:
            raw_tags = row["tag_name"].strip('{}')  
            tag_names = [tag.strip('"') for tag in raw_tags.split(',')]  
            
            for tag in tag_names:
                listing_dicts.append({"tag_name": tag, "tag_count": row["tag_count"]})
        final_listings = []

        for tag_entry in listing_dicts:
            if len(final_listings) < 7:  
                final_listings.append(tag_entry["tag_name"])
            else:
                break

        print("Final Processed Tags:", final_listings)  

    return jsonify(final_listings)

# -----------------------------------------------------------------------------------------
# [GET] colours
@blueprint.route("/getColours")
def getColours():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "colours"')
        colours_data = cursor.fetchall()

    if not colours_data:
        return jsonify([])

    return jsonify(colours_data)

# -----------------------------------------------------------------------------------------
# [GET] specialColours
@blueprint.route("/getSpecialColours")
def getSpecialColours():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "specialColours"')
        allSpecialColours = cursor.fetchall()

    if not allSpecialColours:
        return jsonify([])

    return jsonify(allSpecialColours)

# -----------------------------------------------------------------------------------------
# [GET] languages
@blueprint.route("/getLanguages")
def getLanguages():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "languages"')
        languages = cursor.fetchall()

    if not languages:
        return jsonify([])

    return jsonify(languages)

# -----------------------------------------------------------------------------------------
# [GET] servingTypes
@blueprint.route("/getServingTypes")
def getServingTypes():
    conn = g.db

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "servingTypes"')
        serving_types_data = cursor.fetchall()

    if not serving_types_data:
        return jsonify([])
    
    return jsonify(serving_types_data), 200

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# [GET] producersProfileViews
@blueprint.route("/getProducersProfileViews")
def getProducersProfileViews():
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM "producersProfileViews"')
        producers_profile_views_data = cur.fetchall()

        if not producers_profile_views_data:
            return jsonify([])

        return jsonify(producers_profile_views_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the profile views."
            }
        ), 500
    
    finally:
        cur.close()

# [GET] producersProfileViews by producerID
@blueprint.route("/getProducersProfileViewsByProducer/<id>")
def getProducersProfileViewsByProducer():
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM "producersProfileViews" WHERE "producerID" = %s', (id,))
        producers_profile_views_data = cur.fetchall()

        if not producers_profile_views_data:
            return jsonify([]), 404

        return jsonify(producers_profile_views_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the profile views."
            }
        ), 500
    
    finally:
        cur.close()

# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] producersProfileViews
# @blueprint.route("/getProducersProfileViews")
# def getProducersProfileViews():
#     db = g.db
#     profile_views_data = db.producersProfileViews.find({})
#     allProfileViews = []
#     for profile_view in profile_views_data:
#         # Fetch related views data based on the id(s) in profile_view's views
#         views_data = db.producersProfileViewsViews.find({
#             "_id": {"$in": profile_view['views']}
#         })
#         profile_view['views'] = list(views_data)
#         allProfileViews.append(profile_view)
#     return parse_json(allProfileViews)

# # [GET] producersProfileViews by producerID
# @blueprint.route("/getProducersProfileViewsByProducer/<id>")
# def getProducersProfileViewsByProducer(id):
#     db = g.db
#     profile_views_data = db.producersProfileViews.find({"producerID": ObjectId(id)})
#     allProfileViews = []
#     for profile_view in profile_views_data:
#         # Fetch related views data based on the id(s) in profile_view's views
#         views_data = db.producersProfileViewsViews.find({
#             "_id": {"$in": profile_view['views']}
#         })
#         profile_view['views'] = list(views_data)
#         allProfileViews.append(profile_view)
    # return parse_json(allProfileViews)

# =======================================================

# -----------------------------------------------------------------------------------------

# ================== POSTGRESQL FORMAT ==================

# ----------------------
# [OLD] TO BE DELETED:
# ----------------------

# [GET] venuesProfileViews
@blueprint.route("/getVenuesProfileViews")
def getVenuesProfileViews():
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM "venuesProfileViews"')
        profile_views_data = cur.fetchall()

        if not profile_views_data:
            return jsonify([])

        return jsonify(profile_views_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the profile views."
            }
        ), 500
    
    finally:
        cur.close()

# [GET] venuesProfileViews by venueID
@blueprint.route("/getVenuesProfileViewsByVenue/<id>")
def getVenuesProfileViewsByVenue(id):
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM "venuesProfileViews" WHERE "venueId" = %s', (id,))
        profile_views_data = cur.fetchall()

        if not profile_views_data:
            return jsonify([])

        return jsonify(profile_views_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the profile views."
            }
        ), 500
    
    finally:
        cur.close()

# ----------------------
# [NEW] TO BE ADDED:
# ----------------------

# # [GET] venuesProfileViews
# @blueprint.route("/getVenuesProfileViews")
# def getVenuesProfileViews():
#     db = g.db
#     profile_views_data = db.venuesProfileViews.find({})
#     allProfileViews = []
#     for profile_view in profile_views_data:
#         # Fetch related views data based on the id(s) in profile_view's views
#         views_data = db.venuesProfileViewsViews.find({
#             "_id": {"$in": profile_view['views']}
#         })
#         profile_view['views'] = list(views_data)
#         allProfileViews.append(profile_view)
#     return parse_json(allProfileViews)

# # [GET] venuesProfileViews by venueID
# @blueprint.route("/getVenuesProfileViewsByVenue/<id>")
# def getVenuesProfileViewsByVenue(id):
#     db = g.db
#     profile_views_data = db.venuesProfileViews.find({"venueID": ObjectId(id)})
#     allProfileViews = []
#     for profile_view in profile_views_data:
#         # Fetch related views data based on the id(s) in profile_view's views
#         views_data = db.venuesProfileViewsViews.find({
#             "_id": {"$in": profile_view['views']}
#         })
#         profile_view['views'] = list(views_data)
#         allProfileViews.append(profile_view)
#     return parse_json(allProfileViews)

# =======================================================

# -----------------------------------------------------------------------------------------
# [GET] requestInaccuracy by venueID
@blueprint.route("/getRequestInaccuracyByVenue/<id>")
def getRequestInaccuracyByVenue(id):
    # only get requestInaccuracy that has reviewStatus = False
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM "requestInaccuracy" WHERE "venueId" = %s AND "reviewStatus" = FALSE', (id,))
        request_inaccuracy_data = cur.fetchall()

        if not request_inaccuracy_data:
            return jsonify([])

        return jsonify(request_inaccuracy_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the request inaccuracy."
            }
        ), 500
    
    finally:
        cur.close()

# -----------------------------------------------------------------------------------------
# [GET] Badges
@blueprint.route("/getBadges")
def getBadges():
    conn = g.db
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM "badges"')
        badges_data = cursor.fetchall()

    if not badges_data:
        return jsonify([])

    return jsonify(badges_data)

# -----------------------------------------------------------------------------------------
# [GET] Specific Token
@blueprint.route("/getToken/<token>")
def getToken(token):
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM "tokens" WHERE "token" = %s
        """, (token,))

        token_data = cur.fetchone()

        if token_data is None:
            return jsonify({
                "code": 404,
                "message": "Token not found."
            }), 404
        
        if token_data['userId'] is not None:
            user_id = token_data['userId']
        elif token_data['producerId'] is not None:
            user_id = token_data['producerId']
        elif token_data['venueId'] is not None:
            user_id = token_data['venueId']
        else:
            return jsonify({
                "code": 500,
                "message": "Token does not have a valid associated user."
            }), 500
        
        response_data = {
            "id": token_data['id'],
            "token": token_data['token'],
            "requestId": token_data['requestId'],
            "expiry": token_data['expiry'],
            "userId": user_id
        }

        
        return jsonify({
            "code": 200,
            "data": response_data
        }), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the token."
            }
        ), 500
    
    finally:
        cur.close()

@blueprint.route("/getTokenByRequestId/<requestId>")
def getTokenByRequestId(requestId):
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM "tokens" WHERE "requestId" = %s
        """, (requestId,))
        token_data = cur.fetchone()

        if token_data is None:
            return jsonify({
                "code": 404,
                "message": "Token not found."
            }), 404
        
        if token_data['userId'] is not None:
            user_id = token_data['userId']
        elif token_data['producerId'] is not None:
            user_id = token_data['producerId']
        elif token_data['venueId'] is not None:
            user_id = token_data['venueId']
        else:
            return jsonify({
                "code": 500,
                "message": "Token does not have a valid associated user."
            }), 500
        
        response_data = {
            "id": token_data['id'],
            "token": token_data['token'],
            "requestId": token_data['requestId'],
            "expiry": token_data['expiry'],
            "userId": user_id
        }

        return jsonify({
            "code": 200,
            "data": response_data
        }), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the token."
            }
        ), 500
    
    finally:
        cur.close()

# -----------------------------------------------------------------------------------------
# [GET] Specific Request
@blueprint.route("/getAccountRequest/<id>")
def getAccountRequest(id):
    conn = g.db
    cur = conn.cursor()
    try:
        # check if theres parameters, only for profile + profile settings, will it send this
        if request.args:
            businessType = request.args.get('businessType')  # e.g. ?businessType=venue

            cur.execute("""
                SELECT * FROM "accountRequests" WHERE "businessId" = %s AND "businessType" = %s
            """, (id, businessType,))

        else:
            cur.execute("""
                SELECT * FROM "accountRequests" WHERE "id" = %s
            """, (id,))

        request_data = cur.fetchone()

        if request_data is None:
            return jsonify([]), 200
        
        return jsonify(request_data), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the request."
            }
        ), 500
    
    finally:
        cur.close()

# -----------------------------------------------------------------------------------------
# [GET] Producers
@blueprint.route("/getUsernames")
def getUsernames():
    conn = g.db
    cur = conn.cursor()

    try:
        cur.execute('SELECT "username" FROM "producers"')
        producer_usernames = cur.fetchall()

        cur.execute('SELECT "username" FROM "venues"')
        venue_usernames = cur.fetchall()

        # Combine and filter usernames
        usernames = (
            [username['username'] for username in producer_usernames] +
            [username['username'] for username in venue_usernames]
        )
        usernames = [username for username in usernames if username]  # Filter out any None values

        return jsonify(usernames), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving usernames."
            }
        ), 500
    
    finally:
        cur.close()


# -----------------------------------------------------------------------------------------
# [GET] Any User Regardless of Type by Email
@blueprint.route("/getUserByEmail/<email>")
def getUserByEmail(email):
    conn = g.db
    cur = conn.cursor()

    # Define return data
    return_data = None

    try:
        # Check if user is a user and retrieve the id 
        cur.execute('SELECT * FROM "users" WHERE "email" = %s', (email,))
        user_data = cur.fetchone()

        if user_data is not None:
            return_data = {'id': user_data['id'], 'type': 'user', 'username': user_data['username']}
            
            return jsonify(return_data), 200
        
        # Check if user is a producer and retrieve the id
        cur.execute('SELECT * FROM "producers" WHERE "email" = %s', (email,))
        producer_data = cur.fetchone()

        if producer_data is not None:
            return_data = {'id': producer_data['id'], 'type': 'producer', 'username': producer_data['username']}
            
            return jsonify(return_data), 200
        
        # Check if user is a venue and retrieve the id
        cur.execute('SELECT * FROM "venues" WHERE "email" = %s', (email,))
        venue_data = cur.fetchone()

        if venue_data is not None:
            return_data = {'id': venue_data['id'], 'type': 'venue', 'username': venue_data['username']}
            
            return jsonify(return_data), 200
        
        return jsonify(
            {
                "code": 404,
                "message": "Email not found."
            }
        ), 404
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": str(e)
            }
        ), 500
    
    finally:
        cur.close()


# -----------------------------------------------------------------------------------------
# [GET] A list of users a specific user is following
# @param id: The id of the user
# @return: A list of users the user is following and their photos
# Used: CreateClub.vue (frontend/src/views/Users/CreateClub.vue)
@blueprint.route("/getUserFollowList/<id>")
def getUserFollowList(id):
    conn = g.db
    cur = conn.cursor()

    try:
        # Step 1: Check if id is a valid user in the table based on userType
        cur.execute('SELECT * FROM "users" WHERE "id" = %s', (id,))
        user_data = cur.fetchone()

        if user_data is None:
            return jsonify(
                {
                    "code": 404,
                    "message": "User not found."
                }
            ), 404
        
        # Step 2: Retrieve the follow list using the fetch_user_follow_list function
        follow_list = fetch_follow_lists(cur, id)


        return_data = {
            'users': {}, # A dictionary of objects containing the id, displayName, and photo of the users in the follow list
        }

        # Step 3: Get the id, displayName and photo of the users in the follow list
        for user in follow_list['users']:
            cur.execute('SELECT "id", "displayName", "photo" FROM "users" WHERE "id" = %s', (user,))
            user = cur.fetchone()

            return_data['users'][user['id']] = { 'displayName': user['displayName'], 'photo': user['photo'] }

        return jsonify({
            'followList': return_data
        }), 200

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving the follow list."
            }
        ), 500
    
    finally:
        cur.close()

# -----------------------------------------------------------------------------------------
# [GET] All the usernames in the database [users only]
@blueprint.route("/getAllUsernames")
def getAllUsernames():
    conn = g.db
    cur = conn.cursor()

    try:
        # Step 1: Get all the usernames from the users table
        cur.execute('SELECT "username" FROM "users"')
        user_usernames = cur.fetchall()

        if not user_usernames:
            return jsonify({
                "message": "No usernames found."
            }), 404
        
        return jsonify({
            "usernames": [username['username'] for username in user_usernames]
        }), 200
    
    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred retrieving usernames."
            }
        ), 500
    
    finally:
        cur.close()


# -----------------------------------------------------------------------------------------
# [GET] Check if a user is in the follow list of another user
@blueprint.route("/checkUserInFollowList/<userId>/<userType>/<followId>/<followType>")
def checkUserInFollowList(userId, userType, followId, followType):
    conn = g.db
    cur = conn.cursor()

    try:
        # Step 1: Check if userId and followId are valid users in the table based on userType and followType
        if userType == 'user':
            cur.execute('SELECT * FROM "users" WHERE "id" = %s', (userId,))
        elif userType == 'producer':
            cur.execute('SELECT * FROM "producers" WHERE "id" = %s', (userId,))
        else:
            cur.execute('SELECT * FROM "venues" WHERE "id" = %s', (userId,))
        user_data = cur.fetchone()

        if user_data is None:
            return jsonify(
                {
                    "code": 404,
                    "message": "User not found."
                }
            ), 404

        if followType == 'user':
            cur.execute('SELECT * FROM "users" WHERE "id" = %s', (followId,))
        elif followType == 'producer':
            cur.execute('SELECT * FROM "producers" WHERE "id" = %s', (followId,))
        else:
            cur.execute('SELECT * FROM "venues" WHERE "id" = %s', (followId,))
        follow_data = cur.fetchone()
        
        if follow_data is None:
            return jsonify(
                {
                    "code": 404,
                    "message": "Follow user not found."
                }
            ), 404
        
        # Step 2: Retrieve the follow list of the user
        if followType == 'venue':
            cur.execute('SELECT venues FROM "usersFollowLists" WHERE "userId" = %s', (userId,))
        elif followType == 'producer':
            cur.execute('SELECT producers FROM "usersFollowLists" WHERE "userId" = %s', (userId,))
        else:
            cur.execute('SELECT users FROM "usersFollowLists" WHERE "userId" = %s', (userId,))
        follow_list = cur.fetchone()

        if follow_list is None:
            return jsonify(
                {
                    "code": 404,
                    "message": "Follow list not found."
                }
            ), 404
        
        # Step 3: Check if the followId is in the follow list of the userId
        if followId in follow_list['venues']:
            return jsonify(
                {
                    "code": 200,
                    "following": True
                }
            ), 200
        
        return jsonify(
            {
                "code": 404,
                "following": False
            }
        ), 404

    except Exception as e:
        print(str(e))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred checking the follow list."
            }
        ), 500
    
    finally:
        cur.close()


# -----------------------------------------------------------------------------------------
# [GET] Get news from https://88bamboo.co/blogs/news.atom and convert from RSS to JSON //parse_rss funciton 
@blueprint.route("/getLatestNews", methods=['GET'])
def getLatestNews():
    """API endpoint to fetch RSS data and return it as JSON."""
    rss_url = "https://88bamboo.co/blogs/news.atom"

    try:
        rss_json = parse_rss(rss_url)

         # Add Open Graph images to each news entry
        for entry in rss_json.get("entries", []):
            og_image = get_og_image(entry["link"])
            entry["image"] = og_image if og_image else "https://via.placeholder.com/600x400"  # Place your own placeholder image

        return jsonify(rss_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------------------------------