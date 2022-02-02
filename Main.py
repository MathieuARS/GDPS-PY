import os
import mysql.connector
import itertools
import base64
import requests
import smtplib
import asyncio
import string
import random
import re
import threading
import time
from hashlib import sha1
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from saferproxyfix import SaferProxyFix

load_dotenv(find_dotenv())
mysql_ip = os.environ.get("mysql_ip")
mysql_port = os.environ.get("mysql_port")
mysql_database = os.environ.get("mysql_database")
mysql_user = os.environ.get("mysql_user")
mysql_pass = os.environ.get("mysql_pass")
host = os.environ.get("host")
port = os.environ.get("port")
mail_smtp_server = os.environ.get("mail_smtp_server")
mail_port = os.environ.get("mail_port")
mail_email = os.environ.get("mail_email")
mail_password = os.environ.get("mail_password")
rate_update_webhook = os.environ.get("rate_update_webhook")
encryption_key = bytes(os.environ.get("encryption_key"), encoding='utf-8')
flask_path = os.environ.get("flask_path")
in_production = os.environ.get("in_production")

connection = None
try:
    connection = mysql.connector.connect(host=mysql_ip,
                                         database=mysql_database,
                                         user=mysql_user,
                                         port = int(mysql_port),
                                         password=mysql_pass)
    print("Connected to the DB!")
except:
    print("Couldn't connect to the database.")
    exit()

if connection is None:
    exit()

connection.autocommit = 1
cursor = connection.cursor(buffered=True)
app = Flask(__name__)
app.wsgi_app = SaferProxyFix(app.wsgi_app)

@app.route("/status/", methods=["GET"])
def status():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    return jsonify(ip)

@app.route(f"{flask_path}/accounts/registerGJAccount.php", methods=["POST"])
async def registerAccount():
    userName = request.values.get("userName")
    password = request.values.get("password")
    email = request.values.get("email")
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if not userName or not password or not email or len(userName) > 15 or not bool(re.match("^[A-Za-z0-9]*$", userName)): return "-1"
    cursor = execute_sql("select mail_domain from banned_mails")
    banned_mails = cursor.fetchall()
    for mail in banned_mails:
        if mail[0].lower() in email.lower():
            return "-1"
    cursor = execute_sql("select null from accounts where name = %s or email = %s", [userName, email])
    if cursor.rowcount > 0:
        return "-2"
    if ip is not None and ip != "127.0.0.1":
        cursor = execute_sql("select null from register_ips where ip = %s", [ip])
        if cursor.rowcount == 0:
            cursor = execute_sql("insert into register_ips (ip) values (%s)", [ip])
        else:
            return "-1"
    cipher_suite = Fernet(encryption_key)
    encrypted_password = cipher_suite.encrypt(password.encode())
    verify_token = generate_token()
    cursor = execute_sql("insert into accounts (name,password,email,ip,verify_token,created_on) values (%s,%s,%s,%s,%s,%s)", [userName, encrypted_password, email, request.remote_addr, verify_token, int(time.time())])
    html = f"""\
    <html>
        <body>
            <p>Thank you for creating an account on UltimateGDPS! To activate your account, click the link below:<br>
            <br>
            <a href="https://ultimategdps.mathieuar.fr/auth/verify-account.php?user_name={userName}&verify_token={verify_token}">Verify account</a> 
            </p>
            <p>You are receiving this email because you have created an account on UltimateGDPS</p>
        </body>
    </html>
    """
    threading.Thread(target=send_mail, args=[email, html], daemon=True).start()
    #send_mail(email, html)
    return "1"

@app.route(f"{flask_path}/accounts/loginGJAccount.php", methods=["POST"])
async def loginAccount():
    userName = request.values.get("userName")
    password = request.values.get("password")
    admin_panel = request.values.get("admin_panel")
    if not userName or not password:
        return "-1"

    cursor = execute_sql("select id,password,ban_account from accounts where name = %s", [userName])
    if cursor.rowcount == 0:
        return "-1"
    account_info = cursor.fetchall()[0]
    if account_info[2] == 1:
        if admin_panel != "yes":
            return "-12"
    encrypted_password = account_info[1]
    cipher_suite = Fernet(encryption_key)
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
    if password != decrypted_password:
        return "-1"
    accID = account_info[0]
    if admin_panel == "yes":
        return "1"
    return f"{accID},{accID}"

@app.route(f"{flask_path}/getGJUserInfo20.php", methods=["POST"])
async def getUserInfos():
    targetAccountID = request.values.get("targetAccountID")
    accountID = request.values.get("accountID")
    
    cursor = execute_sql("select null from blocked where user_id = %s and blocked_user_id = %s", [targetAccountID, accountID])
    if cursor.rowcount > 0: return "-1"

    extra_params = None
    cursor = execute_sql("select name,id,coins,user_coins,color1,color2,stars,diamonds,demons,creator_points,privatemsg_status,friendsreq_status,commenthist_status,yt_url,icon_cube,icon_ship,icon_ball,icon_ufo,icon_wave,icon_robot,icon_glow,icon_spider,icon_explosion,twitter_url,twitch_url,verified,ban_account,role from accounts where id = %s", [targetAccountID])
    if cursor.rowcount == 0:
        return "-1"
    infos = cursor.fetchall()[0]
    cursor = execute_sql("SELECT null FROM accounts WHERE stars > %s AND ban_leaderboard = 0 and ban_account = 0 and verified = 1", [infos[6]])
    rank = cursor.rowcount + 1
    mod_badge = 0
    cursor = execute_sql("select badge from roles where id = %s", [infos[27]])
    if cursor.rowcount == 1:
        mod_badge = cursor.fetchall()[0][0]
    if targetAccountID == accountID:
        cursor = execute_sql("select null from private_messages where to_id = %s and is_new = 1", [accountID])
        total_new_msg = cursor.rowcount
        new_friend_count = 0
        cursor = execute_sql("select null from friends where friend1 = %s and is_new1 = 1", [accountID])
        new_friend_count += cursor.rowcount
        cursor = execute_sql("select null from friends where friend2 = %s and is_new2 = 1", [accountID])
        new_friend_count += cursor.rowcount
        cursor = execute_sql("select null from friend_requests where req_user_id = %s and is_new = 1", [accountID])
        friend_requests = cursor.rowcount
        extra_params = f":38:{total_new_msg}:39:{friend_requests}:40:{str(new_friend_count)}"
    if infos[26] == 1:
        return f"1:{infos[0]}:2:{infos[1]}:13:{infos[2]}:17:0:10:0:11:3:3:0:46:{infos[7]}:4:0:8:0:18:2:19:1:50:2:21:{infos[14]}:22:{infos[15]}:23:{infos[16]}:24:{infos[17]}:25:{infos[18]}:26:{infos[19]}:28:{infos[20]}:43:{infos[21]}:47:{infos[22]}:30:0:16:{infos[1]}:31:0:29:0:49:{mod_badge}"

    return f"1:{infos[0]}:2:{infos[1]}:13:{infos[2]}:17:{infos[3]}:10:{infos[4]}:11:{infos[5]}:3:{infos[6]}:46:{infos[7]}:4:{infos[8]}:8:{infos[9]}:18:{infos[10]}:19:{infos[11]}:50:{infos[12]}:20:{infos[13]}:21:{infos[14]}:22:{infos[15]}:23:{infos[16]}:24:{infos[17]}:25:{infos[18]}:26:{infos[19]}:28:{infos[20]}:43:{infos[21]}:47:{infos[22]}:30:{rank}:16:{infos[1]}:31:0:44:{infos[23]}:45:{infos[24]}:29:{infos[25]}:49:{mod_badge}{extra_params}"

@app.route(f"{flask_path}/getGJAccountComments20.php", methods=["POST"])
async def getUserProfileComments():
    print("entré dans getprofilecomment")
    accountID = request.values.get("accountID")
    page = request.values.get("page")
    commentpage = int(page)*10
    cursor = execute_sql("select ban_account,ban_profilemsg,verified,ban_account_reason from accounts where id = %s", [accountID])
    if cursor.rowcount == 0:
        return "-1"
    ban_checks = cursor.fetchall()[0]
    is_accbanned = ban_checks[0]
    is_profilemsgbanned = ban_checks[1]
    is_verified = ban_checks[2]
    ban_account_reason = ban_checks[3]
    if is_accbanned == 1:
        message = f"**Ultimate GDPS** This account is banned. Reason: {ban_account_reason}"
        message = message.encode("ascii")
        message = base64.b64encode(message).decode()
        return f"2~{message}~3~{accountID}~4~test~5~0~7~0~9~Message from Ultimate GDPS#1:0:10"
    if is_profilemsgbanned == 1:
        message = "KipVbHRpbWF0ZSBHRFBTKiogVGhpcyBhY2NvdW50IGlzIG5vdCB2ZXJpZmllZC4gSWYgeW91IGFyZSB0aGUgb3duZXIgb2YgdGhpcyBhY2NvdW50IHlvdSBjYW4gYWN0aXZhdGUgaXQgd2l0aCB0aGUgbGluayBzZW50IHRvIHlvdXIgZW1haWxzLg=="
        return f"2~{message}~3~{accountID}~4~test~5~0~7~0~9~Message from Ultimate GDPS#1:0:10"
    if is_verified == 0:
        message = "**Ultimate GDPS** This account is not verified. If you are the owner of this account you can activate it with the link sent to your emails or it will get deleted in the next 15 minutes."
        message = message.encode("ascii")
        message = base64.b64encode(message).decode()
        return f"2~{message}~3~{accountID}~4~test~5~0~7~0~9~Message from Ultimate GDPS\x04#1:0:10"
    cursor = execute_sql("select comment,likes,is_spam,id,posted_on from acc_comments where account_id = %s order by posted_on desc limit 10 offset %s", [accountID, commentpage])
    comm_count = cursor.rowcount
    if comm_count == 0:
        return "#0:0:0"
    comments_list = cursor.fetchall()
    comments = ""
    for comm in comments_list:
        comments = f"{comments}2~{comm[0]}~3~{accountID}~4~{comm[1]}~5~0~7~{comm[2]}~9~{comm[4]}~6~{comm[3]}|"
    return f"{comments}#{comm_count}:{commentpage}:10"

@app.route(f"{flask_path}/uploadGJAccComment20.php", methods=["POST"])
async def uploadProfileComment():
    comment = request.values.get("comment")
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("insert into acc_comments (account_id,comment) values (%s,%s)", [accountID, comment])
    return "1"

@app.route(f"{flask_path}/getGJUsers20.php", methods=["POST"])
async def getUsers():
    str = request.values.get("str")
    page = request.values.get("page")
    usrpage = int(page)*10
    cursor = execute_sql("SELECT name,id,coins,user_coins,icon_cube,color1,color2,icon_type,special,stars,creator_points,demons FROM accounts WHERE id = %s OR name LIKE CONCAT('%', %s, '%') ORDER BY stars DESC LIMIT 10 OFFSET %s", [str, str, usrpage])
    user_count = cursor.rowcount
    if user_count == 0:
        return "-1"
    users_list = ""
    users = cursor.fetchall()
    count = 1
    for user in users:
        users_list = f"{users_list}1:{user[0]}:2:{user[1]}:13:{user[2]}:17:{user[3]}:9:{user[4]}:10:{user[5]}:11:{user[6]}:14:{user[7]}:15:{user[8]}:16:{user[1]}:3:{user[9]}:8:{user[10]}:4:{user[11]}"
        if count != user_count:
            users_list = users_list + "|"
        count =+ 1
    return f"{users_list}#{user_count}:{usrpage}:10"

@app.route(f"{flask_path}/updateGJUserScore22.php", methods=["POST"])
async def updateUserScore():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    coins = request.values.get("coins")
    stars = request.values.get("stars")
    demons = request.values.get("demons")
    icon = request.values.get("icon")
    color1 = request.values.get("color1")
    color2 = request.values.get("color2")
    iconType = request.values.get("iconType")
    userCoins = request.values.get("userCoins")
    special = request.values.get("special")
    accIcon = request.values.get("accIcon")
    accShip = request.values.get("accShip")
    accBall = request.values.get("accBall")
    accBird = request.values.get("accBird")
    accDart = request.values.get("accDart")
    accRobot = request.values.get("accRobot")
    accGlow = request.values.get("accGlow")
    accSpider = request.values.get("accSpider")
    accExplosion = request.values.get("accExplosion")
    diamonds = request.values.get("diamonds")
    cursor = execute_sql("select verified from accounts where id = %s", [accountID])
    is_verified = cursor.fetchall()[0][0]
    if is_verified == 0: return accountID
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    
    values = [coins, stars, demons, icon, color1, color2, iconType, userCoins, special, accIcon, accShip, accBall, accBird, accDart, accRobot, accGlow, request.remote_addr, accSpider, accExplosion, diamonds, accountID]
    for value in values:
        if value is None:
            return "-1"
    cursor = execute_sql("update accounts set coins=%s,stars=%s,demons=%s,icon=%s,color1=%s,color2=%s,icon_type=%s,user_coins=%s,special=%s,icon_cube=%s,icon_ship=%s,icon_ball=%s,icon_ufo=%s,icon_wave=%s,icon_robot=%s,icon_glow=%s,ip=%s,icon_spider=%s,icon_explosion=%s,diamonds=%s where id = %s", values)
    return accountID

@app.route(f"{flask_path}/getGJScores20.php", methods=["POST"])
async def getLeaderboardScores():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    type = request.values.get("type")
    cursor = execute_sql("select ban_account,verified,stars from accounts where id = %s", [accountID])
    infos = cursor.fetchall()[0]
    is_banned =infos[0]
    is_verified = infos[1]
    stars = infos[2]
    if is_banned == 1:
        return "-1"
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    users_list = None
    needed_infos = "name,id,coins,user_coins,icon,color1,color2,icon_type,special,stars,creator_points,demons,diamonds"
    count = 1
    print(type)
    if type == "top":
        cursor = execute_sql("SELECT " + needed_infos + " FROM accounts WHERE ban_leaderboard = 0 and verified = '1' AND stars > '0' ORDER BY stars DESC LIMIT 100")
        users_list = cursor.fetchall()
    elif type == "creators":
        cursor = execute_sql("SELECT " + needed_infos + " FROM accounts WHERE ban_leaderboard = 0 and verified = '1' and creator_points > '0' ORDER BY creator_points DESC LIMIT 100")
        users_list = cursor.fetchall()
    elif type == "relative":
        if is_verified == 0:
            return "-1"
        users_list = []
        cursor = execute_sql("SELECT id FROM accounts WHERE stars > %s AND ban_leaderboard = 0 and ban_account = 0 and verified = 1 ORDER BY stars DESC", [stars])
        total_up = cursor.fetchall()
        cursor = execute_sql("SELECT " + needed_infos + " FROM accounts WHERE stars > %s AND ban_leaderboard = 0 and verified = 1 and id != %s ORDER BY stars DESC LIMIT 50", [stars, accountID])
        if cursor.rowcount > 0:
            users_list = cursor.fetchall()
            for id in total_up:
                if id[0] == users_list[0][1]:
                    break
                count += 1
        cursor = execute_sql("select " + needed_infos + " from accounts where id = %s", [accountID])
        users_list.append(cursor.fetchall()[0])
        cursor = execute_sql("SELECT " + needed_infos + " FROM accounts WHERE stars <= %s AND ban_leaderboard = 0 and verified = 1 and id != %s ORDER BY stars DESC LIMIT 50", [stars, accountID])
        if cursor.rowcount > 0:
            users_list.append(cursor.fetchall()[0])
    elif type == "friends":
        cursor = execute_sql("select friend1,friend2 from friends where friend1 = %s or friend2 = %s", [accountID, accountID])
        if cursor.rowcount == 0: return "-1"
        friends_list = cursor.fetchall()
        friends = f"{accountID}"
        for friend in friends_list:
            friend_id = friend[0]
            if str(friend[0]) == accountID:
                friend_id = friend[1]
            friends = f"{friends},{friend_id}"
        cursor = execute_sql("SELECT " + needed_infos + " FROM accounts WHERE ban_leaderboard = 0 and verified = 1 and id in (" + friends + ") ORDER BY stars DESC")
        users_list = cursor.fetchall()
    else:
        return "-1"

    if users_list is None:
        return "-1"
    lead_list = ""
    for user in users_list:
        lead_list = f"{lead_list}1:{user[0]}:2:{user[1]}:13:{user[2]}:17:{user[3]}:6:{count}:9:{user[4]}:10:{user[5]}:11:{user[6]}:14:{user[7]}:15:{user[8]}:16:{user[1]}:3:{user[9]}:8:{user[10]}:4:{user[11]}:7:{user[1]}:46:{user[12]}|"
        count += 1
    return lead_list

@app.route(f"{flask_path}/uploadGJLevel21.php", methods=["POST"])
async def uploadLevel():
    gjp = request.values.get("gjp")
    gameVersion = request.values.get("gameVersion")
    levelDesc = request.values.get("levelDesc")
    levelName = request.values.get("levelName")
    levelString = request.values.get("levelString")
    levelVersion = request.values.get("levelVersion")
    levelLength = request.values.get("levelLength")
    audioTrack = request.values.get("audioTrack")
    password = request.values.get("password")
    original = request.values.get("original")
    twoPlayer = request.values.get("twoPlayer")
    songID = request.values.get("songID")
    objects = request.values.get("objects")
    coins = request.values.get("coins")
    requestedStars = request.values.get("requestedStars")
    unlisted = request.values.get("unlisted")
    ldm = request.values.get("ldm")
    accountID = request.values.get("accountID")
    levelInfo = request.values.get("levelInfo")
    binaryVersion = request.values.get("binaryVersion")
    extraString = request.values.get("extraString")

    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    args = [levelName, gameVersion, binaryVersion, levelString, levelDesc, levelVersion, levelLength, audioTrack, password, original, twoPlayer, songID, objects, coins, requestedStars, extraString, levelInfo, accountID, unlisted, ldm]
    
    cursor = execute_sql("SELECT id FROM levels WHERE name = %s AND author_id = %s", [levelName, accountID])
    level_id = None
    try:
        level_id = cursor.fetchall()[0][0]
    except:
        pass
    if cursor.rowcount == 0:
        cursor = execute_sql("insert into levels (name,game_version,binary_version,level_content,description,version,length,official_song,password,original,dual_mode,custom_song,objects,coins,requested_rate,extra_content,level_info,author_id,unlisted,ldm) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", args)
        cursor = execute_sql("SELECT id FROM levels WHERE name = %s AND author_id = %s", [levelName, accountID])
        level_id = cursor.fetchall()[0][0]
    elif cursor.rowcount == 1:
        cursor = execute_sql("update levels set game_version=%s,binary_version=%s,level_content=%s,description=%s,version = version + 1,length=%s,official_song=%s,password=%s,dual_mode=%s,custom_song=%s,objects=%s,coins=%s,requested_rate=%s,extra_content=%s,level_info=%s,unlisted=%s,ldm=%s where id = %s", [gameVersion, binaryVersion, levelString, levelDesc, levelLength, audioTrack, password, twoPlayer, songID, objects, coins, requestedStars, extraString, levelInfo, unlisted, ldm, level_id])
    else:
        return "-1"
    return str(level_id)

@app.route(f"{flask_path}/getGJLevels21.php", methods=["POST"])
async def getLevels():
    gd_type = request.values.get("type")
    accountID = request.values.get("accountID")
    gd_str = request.values.get("str")
    page = 0
    if "page" in request.values:
        page = int(request.values.get("page"))*10
    gauntlet_id = request.values.get("gauntlet")
    gauntlet = False
    if gauntlet_id is not None and gauntlet_id != "": gauntlet = True
    print(request.values)
    levels = ""
    users = ""
    songs = ""
    all_levels = ""
    count = 0
    total_levels = 0
    lvl_ids = []
    needed_infos = "id,name,version,author_id,difficulty,downloads,official_song,game_version,likes,demon,demon_difficulty,auto,stars,featured,epic,objects,description,length,original,coins,coins_verified,requested_rate,ldm,custom_song"
    if gd_type == "0":
        gd_str = f"%{gd_str}%"
        base_query = " from levels where name like %s or id like %s"
        cursor = execute_sql("select null" + base_query, [gd_str, gd_str])
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by downloads desc limit 10 offset %s", [gd_str, gd_str, page])
    elif gd_type == "1":
        base_query = " from levels where unlisted != 1"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by downloads desc limit 10 offset %s", [page])
    elif gd_type == "2":
        base_query = " from levels where unlisted != 1"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by likes desc limit 10 offset %s", [page])
    elif gd_type == "4":
        base_query = " from levels where unlisted != 1"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date desc limit 10 offset %s", [page])
    elif gd_type == "5":
        base_query = " from levels where author_id = %s"
        cursor = execute_sql("select null" + base_query, [gd_str])
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [gd_str, page])
    elif gd_type == "6":
        base_query = " from levels where unlisted != 1 and featured = 1"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [page])
    elif gd_type == "7":
        base_query = " from levels where unlisted != 1 and objects > 9999"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [page])
    elif gd_type == "10":
        check = re.match(r"^[0-9,]*$", gd_str)
        if not check: return "-1"
        base_query = " from levels where id in (" + gd_str + ")"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [page])
    elif gd_type == "11":
        base_query = " from levels where unlisted != 1 and stars > 0"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [page])
    elif gd_type == "16":
        base_query = " from levels where unlisted != 1 and epic > 0"
        cursor = execute_sql("select null" + base_query)
        if cursor.rowcount == 0: return "-1"
        else: total_levels = cursor.rowcount
        cursor = execute_sql("select " + needed_infos + base_query + " order by upload_date limit 10 offset %s", [page])
    elif gauntlet:
        base_query = " from levels where id = %s"
        cursor = execute_sql("select lvl1,lvl2,lvl3,lvl4,lvl5 from gauntlets where id = %s", [gauntlet_id])
        if cursor.rowcount == 0: return "-1"
        total_levels = 5
        gl_levels = cursor.fetchall()[0]
        cursor = execute_sql("select " + needed_infos + base_query + " union select " + needed_infos + base_query + " union select " + needed_infos + base_query + " union select " + needed_infos + base_query + " union select " + needed_infos + base_query, [gl_levels[0],gl_levels[1],gl_levels[2],gl_levels[3],gl_levels[4]])
    else:
        return "-1"
    all_levels = cursor.fetchall()
    scount = 0
    for lvl in all_levels:
        if lvl[23] > 0:
            scount += 1

    rs_count = 0
    for lvl in all_levels:
        count += 1
        levels = f"{levels}1:{lvl[0]}:2:{lvl[1]}:5:{lvl[2]}:6:{lvl[3]}:8:10:9:{lvl[4]}:10:{lvl[5]}:12:{lvl[6]}:13:{lvl[7]}:14:{lvl[8]}:17:{lvl[9]}:43:{lvl[10]}:25:{lvl[11]}:18:{lvl[12]}:19:{lvl[13]}:42:{lvl[14]}:45:{lvl[15]}:3:{lvl[16]}:15:{lvl[17]}:30:{lvl[18]}:31:0:37:{lvl[19]}:38:{lvl[20]}:39:{lvl[21]}:46:1:47:2:40:{lvl[22]}:35:{lvl[23]}"
        if gauntlet: levels = f"{levels}:44:{gauntlet_id}"
        author_name = get_user_name(lvl[3])
        author_id = lvl[3]
        if author_name is None:
            author_name = ""
            author_id = "0"
        users = f"{users}{lvl[3]}:{author_name}:{author_id}"
        lvl_ids.append(lvl[0])
        song_id = lvl[23]
        if song_id > 0:
            encoded_song = get_encode_song(song_id)
            if "~" in encoded_song:
                songs = f"{songs}{encoded_song}"
                rs_count += 1
        if count != len(all_levels):
            levels = levels + "|"
            users = users + "|"
            if song_id > 0 and "~" in encoded_song and rs_count < scount:
                songs = songs + "~:~"
    cursor = execute_sql("select null from levels")
    count = cursor.rowcount
    if page == 0:
        page = "00"
    levels_hash = get_levels_hash(lvl_ids)
    response = f"{levels}#{users}#{songs}#{total_levels}:{page}:10#{levels_hash}"
    return response

@app.route(f"{flask_path}/getGJSongInfo.php", methods=["POST"])
async def getSongInfos():
    songID = request.values.get("songID")
    return get_encode_song(songID)

@app.route(f"{flask_path}/downloadGJLevel22.php", methods=["POST"])
async def downloadLevel():
    levelID = request.values.get("levelID")
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    print(request.values)

    if accountID is not None and accountID != "":
        gjp_check = check_gjp(accountID, gjp)
        if gjp_check: 
            cursor = execute_sql("select null from actions where value1 = %s and value2 = %s and type = 'download'", [accountID, levelID])
            if cursor.rowcount == 0:
                cursor = execute_sql("update levels set downloads = downloads + 1 where id = %s", [levelID])
                cursor = execute_sql("insert into actions (type,value1,value2) values (%s,%s,%s)", ["download", accountID, levelID])
    cursor = execute_sql("select id,name,description,level_content,version,author_id,difficulty,downloads,official_song,game_version,likes,demon,demon_difficulty,auto,stars,featured,epic,objects,length,original,upload_date,update_date,custom_song,extra_content,coins,coins_verified,requested_rate,ldm,password from levels where id = %s", [levelID])
    if cursor.rowcount == 0:
       return "-1"
    lvl_infos = cursor.fetchall()[0]
    lvl_string = lvl_infos[3]
    level_pass = lvl_infos[28]
    xorpass = 0
    if level_pass != 0:
        xorpass = b64_encode(xor_cipher(str(level_pass), "26364"))
    upload_date = "19-10-2021 15-42"
    update_date = "blopu"
    response = f"1:{lvl_infos[0]}:2:{lvl_infos[1]}:3:{lvl_infos[2]}:4:{lvl_infos[3]}:5:{lvl_infos[4]}:6:{lvl_infos[5]}:8:10:9:{lvl_infos[6]}:10:{lvl_infos[7]}:11:1:12:{lvl_infos[8]}:13:{lvl_infos[9]}:14:{lvl_infos[10]}:17:{lvl_infos[11]}:43:{lvl_infos[12]}:25:{lvl_infos[13]}:18:{lvl_infos[14]}:19:{lvl_infos[15]}:42:{lvl_infos[16]}:45:{lvl_infos[17]}:15:{lvl_infos[18]}:30:{lvl_infos[19]}:31:1:28:{upload_date}:29:{update_date}:35:{lvl_infos[22]}:36:{lvl_infos[23]}:37:{lvl_infos[24]}:38:{lvl_infos[25]}:39:{lvl_infos[26]}:46:1:47:2:48:1:40:{lvl_infos[27]}:27:{xorpass}"
    encoded_string = get_encoded_lvlstring(lvl_string)
    lvl_moreinfos = f"{lvl_infos[5]},{lvl_infos[14]},{lvl_infos[11]},{lvl_infos[0]},{lvl_infos[25]},{lvl_infos[15]},{lvl_infos[28]},0"
    encoded_lvlinfos = sha1(f"{lvl_moreinfos}xI25fpAapCQg".encode()).hexdigest()
    cursor = execute_sql("select name from accounts where id = %s", [lvl_infos[5]])

    return f"{response}#{encoded_string}#{encoded_lvlinfos}#{lvl_moreinfos}"

@app.route(f"{flask_path}/requestUserAccess.php", methods=["POST"])
async def modReq():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("select role from accounts where id = %s", [accountID])
    if cursor.rowcount == 0:
        return "-1"
    role_id = cursor.fetchall()[0][0]
    cursor = execute_sql("select badge from roles where id = %s", [role_id])
    if cursor.rowcount == 0:
        return "-1"
    badge_id = cursor.fetchall()[0][0]
    if badge_id == 0:
        return "-1"
    elif badge_id == 1:
        return "1"
    elif badge_id > 1:
        return "2"
    else:
        return "-1"

@app.route(f"{flask_path}/suggestGJStars20.php", methods=["POST"])
async def ModSents():
    print("oui")
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    levelID = request.values.get("levelID")
    stars = int(request.values.get("stars"))
    feature = int(request.values.get("feature"))
    demon = 0
    auto = 0
    difficulty = 0
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("select role from accounts where id = %s", [accountID])
    if cursor.rowcount == 0:
        return "-1"
    role_id = cursor.fetchall()[0][0]

    cursor = execute_sql("select perm_suggest,perm_rate from roles where id = %s", [role_id])
    if cursor.rowcount == 0:
        return "-1"
    perms = cursor.fetchall()[0]
    data = {}
    image = ""
    if perms[1] == 1:
        if stars == 1:
            auto = 1
            image = "auto"
        elif stars == 2:
            difficulty = 10
            image = "easy"
        elif stars == 3:
            difficulty = 20
            image = "normal"
        elif stars == 4 or stars == 5:
            difficulty = 30
            image = "hard"
        elif stars == 6 or stars == 7:
            difficulty = 40
            image = "harder"
        elif stars == 8 or stars == 9:
            difficulty = 50
            image = "insane"
        elif stars == 10:
            demon = 1
            image = "demon-hard"
        if feature == 1:
            image = f"{image}-featured"
        cursor = execute_sql("select id,name,author_id,downloads,likes,length,description,stars from levels where id = %s", [levelID])
        if cursor.rowcount == 0:
            return "-1"
        lvl_infos = cursor.fetchall()[0]
        cursor = execute_sql("update levels set stars = %s, featured = %s, demon = %s, auto = %s, difficulty = %s where id = %s", [stars, feature, demon, auto, difficulty, levelID])
        print(lvl_infos)

        def send_discord_message():
            cursor = execute_sql("select name from accounts where id = %s", [lvl_infos[2]])
            author_name = cursor.fetchall()[0][0]
            already_rated = False
            if lvl_infos[7] > 0:
                already_rated = True

            time = lvl_infos[5]
            if lvl_infos[6] == "":
                description = "No description provided"
            else:
                description = b64_decode(lvl_infos[6])
            length = "Unknown"
            if time == 0:
                length = "Tiny"
            elif time == 1:
                length = "Short"
            elif time == 2:
                length = "Medium"
            elif time == 3:
                length = "Long"
            elif time == 4:
                length = "XL"
            title = "A new level got rated!"
            if already_rated:
                title = "A level got its rating updated!"
            data = {"embeds": [{"title": title,
                                "description" : f"<:play:900086729120292974> **{lvl_infos[1]}** by {author_name} \n<:comment:900091546299424838> {description} \n<:time:900085839399362570> {length} \n<:download:900085215312093194> {lvl_infos[3]} \n<:like:900085517520109599> {lvl_infos[4]} \n🆔 {lvl_infos[0]}",
                                "color": 65280,
                                "thumbnail": {"url": f"https://mathieuar.fr/gdps_assets/{image}.png"}}]}
            requests.post(rate_update_webhook, json = data)

        threading.Thread(target=send_discord_message, daemon=True).start()
        return "1"

@app.route(f"{flask_path}/uploadGJComment21.php", methods=["POST"])
async def uploadLvlComment():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    comment = request.values.get("comment")
    percent = request.values.get("percent")
    levelID = request.values.get("levelID")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    if comment is None or accountID is None:
        return "-1"
    if percent is None:
        percent = 0
    cursor = execute_sql("insert into lvl_comments (author_id,comment,percent,level_id) values (%s,%s,%s,%s)", [accountID, comment, percent, levelID])
    return "1"

@app.route(f"{flask_path}/deleteGJComment20.php", methods=["POST"])
async def deleteLvlComment():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    commentID = request.values.get("commentID")
    levelID = request.values.get("levelID")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("delete from lvl_comments where id = %s and level_id = %s and author_id = %s", [commentID, levelID, accountID])
    return "1"

@app.route(f"{flask_path}/getGJComments21.php", methods=["POST"])
@app.route(f"{flask_path}/getGJCommentHistory.php", methods=["POST"])
async def getLvlComments():
    print("ok")
    mode = request.values.get("mode")
    levelID = request.values.get("levelID")
    userID = request.values.get("userID")
    page = int(request.values.get("page"))
    count = request.values.get("count")
    if count is None or count == "": count = 10
    count = int(count)
    offset = page*count
    order = "uploaded_on"
    selected_row = "level_id"
    wanted_id = levelID
    if userID is not None and userID != "":
        selected_row = "author_id"
        wanted_id = userID
    if mode == 1:
        order = "likes"
    cursor = execute_sql("select id,uploaded_on,comment,author_id,likes,is_spam,percent,level_id from lvl_comments where " + selected_row + " = %s order by %s desc limit %s offset %s", [wanted_id, order, count, offset])
    if cursor.rowcount == 0:
        return "-2"
    comments = cursor.fetchall()
    comment_string = ""
    total_comm = cursor.rowcount
    count = 1
    for comm in comments:
        cursor = execute_sql("select role,comment_color,name,icon,color1,color2,icon_type,special from accounts where id = %s", [comm[3]])
        user_info = cursor.fetchall()[0]
        badge = "0"
        if user_info[0] != 9999:
            cursor = execute_sql("select badge from roles where id = %s", [user_info[0]])
            badge = cursor.fetchall()[0][0]
        if selected_row == "author_id":
            comment_string = f"{comment_string}1~{comm[7]}~"
        comment_string = f"{comment_string}2~{comm[2]}~3~{comm[3]}~4~{comm[4]}~5~0~7~{comm[5]}~9~{comm[1]}~6~{comm[0]}~10~{comm[6]}~11~{badge}~12~{user_info[1]}:1~{user_info[2]}~7~1~9~{user_info[3]}~10~{user_info[4]}~11~{user_info[5]}~14~{user_info[6]}~15~{user_info[7]}~16~{comm[3]}"
        if count < total_comm:
            comment_string = f"{comment_string}|"
        count += 1
    cursor = execute_sql("select null from levels where id = %s", [levelID])
    total_count = cursor.rowcount
    return f"{comment_string}#{total_count}:{offset}:{total_count}"

@app.route(f"{flask_path}/updateGJAccSettings20.php", methods=["POST"])
async def updateProfile():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    msg = request.values.get("mS")
    friend = request.values.get("frS")
    msg_hist = request.values.get("cS")
    yt = request.values.get("yt")
    twitch = request.values.get("twitch")
    twitter = request.values.get("twitter")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    print(request.values)
    cursor = execute_sql("update accounts set privatemsg_status=%s,friendsreq_status=%s,commenthist_status=%s,yt_url=%s,twitch_url=%s,twitter_url=%s where id = %s", [msg, friend, msg_hist, yt, twitch, twitter, accountID])
    return "1"

@app.route(f"{flask_path}/likeGJItem211.php", methods=["POST"])
async def like():
    accountID = request.values.get("accountID")
    type = int(request.values.get("type"))
    itemID = request.values.get("itemID")
    like = int(request.values.get("like"))
    gjp = request.values.get("gjp")
    print(request.values)
    gjp_check = check_gjp(accountID, gjp)
    action_type = None
    table = None
    if not gjp_check:
        return "-1"
    if type == 1:
        action_type = "lvl_like"
        table = "levels"
    elif type == 2:
        action_type = "lvlcomm_like"
        table = "lvl_comments"
    elif type == 3:
        action_type = "acccomm_like"
        table = "acc_comments"
    else:
        print("returned at type")
        return "-1"

    if like == 0:
        like = -1
    elif like == 1:
        pass
    else:
        print("returned at like")
        return "-1"

    cursor = execute_sql("select null from actions where value1 = %s and value2 = %s and type = %s", [accountID, itemID, action_type])
    if cursor.rowcount == 0:
        cursor = execute_sql("update " + table + " set likes = likes + %s where id = %s", [like, itemID])
        cursor = execute_sql("insert into actions (type,value1,value2) values (%s,%s,%s)", [action_type, accountID, itemID])
    else:
        return "-1"
    return "1"

@app.route(f"{flask_path}/database/accounts/backupGJAccountNew.php", methods=["POST"])
async def saveAccount():
    userName = request.values.get("userName")
    password = request.values.get("password")
    saveData = request.values.get("saveData")
    cursor = execute_sql("select password from accounts where name = %s", [userName])
    if cursor.rowcount == 0 or cursor.rowcount > 1: return "-1"
    encrypted_password = cursor.fetchall()[0][0]
    cipher_suite = Fernet(encryption_key)
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
    if password != decrypted_password: return "-1"
    cursor = execute_sql("update accounts set save_data = %s where name = %s", [saveData, userName])
    return "1"

@app.route(f"{flask_path}/database/accounts/syncGJAccountNew.php", methods=["POST"])
async def loadAccount():
    userName = request.values.get("userName")
    password = request.values.get("password")
    cursor = execute_sql("select password,save_data from accounts where name = %s", [userName])
    if cursor.rowcount == 0 or cursor.rowcount > 1: return "-1"
    user_infos = cursor.fetchall()[0]
    encrypted_password = user_infos[0]
    user_data = user_infos[1]
    cipher_suite = Fernet(encryption_key)
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
    if password != decrypted_password: return "-1"
    return f"{user_data};21;30;a;a"

@app.route(f"{flask_path}/getAccountURL.php", methods=["POST"])
async def getAccountUrl():
    return request.url.replace("/getAccountURL.php", "")

@app.route(f"{flask_path}/rateGJDemon21.php", methods=["POST"])
async def demonRate():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    levelID = request.values.get("levelID")
    rating = request.values.get("rating")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    image = None
    if rating == "1":
        rating = "3"
        image = "demon-easy"
    elif rating == "2":
        rating = "4"
        image = "demon-medium"
    elif rating == "3":
        rating = "0"
        image = "demon-hard"
    elif rating == "4":
        rating = "5"
        image = "demon-insane"
    elif rating == "5":
        rating = "6"
        image = "demon-extreme"
    else:
        return "-1"
    
    demon_rate_name = get_demon_rate_name(rating, "real")
    cursor = execute_sql("select role from accounts where id = %s", [accountID])
    role_id = cursor.fetchall()[0][0]
    if role_id != 9999:
        cursor = execute_sql("select perm_rate from roles where id = %s", [role_id])
        perm = cursor.fetchall()[0][0]
        if perm == 1:
            cursor = execute_sql("select featured,demon_difficulty,name,author_id from levels where id = %s", [levelID])
            result = cursor.fetchall()[0]
            cursor = execute_sql("select name from accounts where id = %s", [result[3]])
            author_name = cursor.fetchall()[0][0]
            old_demon_rate_name = get_demon_rate_name(result[1], "real")
            if result[0] == 1:
                image = f"{image}-featured"
            cursor = execute_sql("update levels set demon_difficulty = %s where id = %s", [rating, levelID])
            data = {"embeds": [{"title": "A level got its demon rating updated!",
                                "description" : f"<:play:900086729120292974> **{result[2]}** by {author_name} \n<:demonupdate:902531596744273970> {old_demon_rate_name} > {demon_rate_name} \n🆔 {levelID}",
                                "color": 16733440,
                                "thumbnail": {"url": f"https://mathieuar.fr/gdps_assets/{image}.png"}}]}
            requests.post(rate_update_webhook, json = data)
    else:
        cursor = execute_sql("select null from actions where type = 'demon_suggestion' and value1 = %s", [accountID])
        if cursor.rowcount == 0:
            cursor = execute_sql("insert into actions (type,value1,value2) values ('demon_suggestion',%s,%s)", [accountID, rating])
        else:
            cursor = execute_sql("update actions set value2 = %s where type = 'demon_suggestion' and value1 = %s", [rating, accountID])
    return str(levelID)

@app.route(f"{flask_path}/getGJGauntlets21.php", methods=["POST"])
async def getGauntlets():
    cursor = execute_sql("select id,lvl1,lvl2,lvl3,lvl4,lvl5 from gauntlets order by id asc")
    if cursor.rowcount == 0: return "0"
    all_gauntlets = cursor.fetchall()
    gauntlet_string = ""
    gauntlet_string2 = ""
    for gauntlet in all_gauntlets:
        lvl = f"{gauntlet[1]},{gauntlet[2]},{gauntlet[3]},{gauntlet[4]},{gauntlet[5]}"
        gauntlet_string = f"{gauntlet_string}1:{gauntlet[0]}:3:{lvl}|"
        gauntlet_string2 = f"{gauntlet_string2}{gauntlet[0]}{lvl}"
    hashed_string = sha1(f"{gauntlet_string2}xI25fpAapCQg".encode()).hexdigest()
    return f"{gauntlet_string}#{hashed_string}"

@app.route(f"{flask_path}/uploadGJMessage20.php", methods=["POST"])
async def sendPrivateMessage():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    toAccountID = request.values.get("toAccountID")
    subject = request.values.get("subject")
    body = request.values.get("body")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    cursor = execute_sql("select privatemsg_status from accounts where id = %s", [toAccountID])
    message_status = cursor.fetchall()[0][0]
    is_friend = False
    if message_status == 1:
        cursor = execute_sql("select null from friends where friend1 = %s and friend2 = %s or friend1 = %s and friend2 = %s", [accountID, toAccountID, toAccountID, accountID])
        if cursor.rowcount > 0:
            is_friend = True
    cursor = execute_sql("select null from blocked where user_id = %s and blocked_user_id = %s", [toAccountID, accountID])
    if cursor.rowcount > 0 or message_status == 2 or is_friend is False:
        return "-1"
    cursor = execute_sql("insert into private_messages (from_id,to_id,subject,body,sent_on) values (%s,%s,%s,%s,%s)", [accountID, toAccountID, subject, body, int(time.time())])
    return "1"

@app.route(f"{flask_path}/getGJMessages20.php", methods=["POST"])
async def getPrivateMessage():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    getSent = request.values.get("getSent")
    page = int(request.values.get("page"))*10
    print(request.values)
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    msg_count = 0
    if getSent is None or getSent == "":
        cursor = execute_sql("select null from private_messages where to_id = %s", [accountID])
        msg_count = cursor.rowcount
        cursor = execute_sql("select id,from_id,subject,sent_on,is_new from private_messages where to_id = %s order by sent_on desc limit 10 offset %s", [accountID, page])
        getSent = 0
    else:
        cursor = execute_sql("select null from private_messages where from_id = %s", [accountID])
        msg_count = cursor.rowcount
        cursor = execute_sql("select id,to_id,subject,sent_on,is_new from private_messages where from_id = %s order by sent_on desc limit 10 offset %s", [accountID, page])
        getSent = 1
    if msg_count == 0: return "-2"

    messages = cursor.fetchall()
    msg_string = ""
    for msg in messages:
        cursor = execute_sql("select name from accounts where id = %s", [msg[1]])
        user_name = cursor.fetchall()[0][0]
        is_new = msg[4]
        if is_new == 1:
            is_new = 0
        else:
            is_new = 1
        msg_string = f"{msg_string}6:{user_name}:3:{msg[1]}:2:{msg[1]}:1:{msg[0]}:4:{msg[2]}:8:{is_new}:9:{getSent}:7:{msg[3]}|"
    return f"{msg_string}#{msg_count}:{page}:10"

@app.route(f"{flask_path}/downloadGJMessage20.php", methods=["POST"])
async def downloadPrivateMessage():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    messageID = request.values.get("messageID")
    isSender = request.values.get("isSender")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    message = ""
    if isSender is None or isSender == "":
        cursor = execute_sql("select from_id,sent_on,subject,is_new,body from private_messages where id = %s and to_id = %s", [messageID, accountID])
        if cursor.rowcount == 0: return "-1"
        message = cursor.fetchall()[0]
        cursor = execute_sql("update private_messages set is_new = 0 where id = %s and to_id = %s", [messageID, accountID])
        isSender = 0
    else:
        cursor = execute_sql("select to_id,sent_on,subject,is_new,body from private_messages where id = %s and from_id = %s", [messageID, accountID])
        if cursor.rowcount == 0: return "-1"
        message = cursor.fetchall()[0]
        isSender = 1
    cursor = execute_sql("select name from accounts where id = %s", [message[0]])
    user_name = cursor.fetchall()[0][0]
    return f"6:{user_name}:3:{message[0]}:2:{message[0]}:1:{messageID}:4:{message[2]}:8:{message[3]}:9:{isSender}:5:{message[4]}:7:{message[1]}"

@app.route(f"{flask_path}/blockGJUser20.php", methods=["POST"])
async def blockUser():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    targetAccountID = request.values.get("targetAccountID")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    cursor = execute_sql("insert into blocked (user_id,blocked_user_id) values (%s,%s)", [accountID, targetAccountID])
    return "1"

@app.route(f"{flask_path}/getGJUserList20.php", methods=["POST"])
async def getUserList():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    gd_type = request.values.get("type")
    gjp_check = check_gjp(accountID, gjp)
    user_list = None
    if not gjp_check:
        return "-1"
    if gd_type == "0":
        cursor = execute_sql("select friend1,friend2,is_new1,is_new2 from friends where friend1 = %s or friend2 = %s", [accountID, accountID])
        if cursor.rowcount == 0:
            return "-2"
        user_list = cursor.fetchall()
    elif gd_type == "1":
        cursor = execute_sql("select blocked_user_id from blocked where user_id = %s", [accountID])
        if cursor.rowcount == 0:
            return "-2"
        user_list = cursor.fetchall()
    else:
        return "-1"
    peoplestring = ""
    for user in user_list:
        if gd_type == "1":
            cursor = execute_sql("select name,icon,color1,color2,icon_type,special from accounts where id = %s", [user[0]])
            user_infos = cursor.fetchall()[0]
            peoplestring = f"{peoplestring}1:{user_infos[0]}:2:{user[0]}:9:{user_infos[1]}:10:{user_infos[2]}:11:{user_infos[3]}:14:{user_infos[4]}:15:{user_infos[5]}:16:{user[0]}:18:0:41:0"
        else:
            user_id = user[0]
            is_new = user[3]
            if accountID == str(user[0]):
                user_id = user[1]
                is_new = user[2]
            cursor = execute_sql("select name,icon,color1,color2,icon_type,special from accounts where id = %s", [user_id])
            user_infos = cursor.fetchall()[0]
            peoplestring = f"{peoplestring}1:{user_infos[0]}:2:{user_id}:9:{user_infos[1]}:10:{user_infos[2]}:11:{user_infos[3]}:14:{user_infos[4]}:15:{user_infos[5]}:16:{user_id}:18:0:41:{is_new}|"
        cursor = execute_sql("update friends set is_new1 = 0 where friend1 = %s", [accountID])
        cursor = execute_sql("update friends set is_new2 = 0 where friend2 = %s", [accountID])
    return peoplestring

@app.route(f"{flask_path}/uploadFriendRequest20.php", methods=["POST"])
async def sendFriendRequest():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    toAccountID = request.values.get("toAccountID")
    comment = request.values.get("comment")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    cursor = execute_sql("select friendsreq_status from accounts where id = %s", [toAccountID])
    friendreq_status = cursor.fetchall()[0][0]
    cursor = execute_sql("select null from blocked where user_id = %s and blocked_user_id = %s", [toAccountID, accountID])
    if cursor.rowcount > 0 or friendreq_status == 1: return "-1"
    cursor = execute_sql("select null from friend_requests where user_id = %s and req_user_id = %s", [accountID, toAccountID])
    if cursor.rowcount > 0: return "-1"
    cursor = execute_sql("insert into friend_requests (user_id,req_user_id,comment,requested_on) values (%s,%s,%s,%s)", [accountID, toAccountID, comment, int(time.time())])
    return "1"

@app.route(f"{flask_path}/getGJFriendRequests20.php", methods=["POST"])
async def getFriendRequests():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    getSent = request.values.get("getSent")
    page = int(request.values.get("page"))*10
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    req_count = 0
    if getSent is None or getSent == "":
        cursor = execute_sql("select null from friend_requests where req_user_id = %s", [accountID])
        req_count = cursor.rowcount
        cursor = execute_sql("select id,user_id,comment,requested_on,is_new from friend_requests where req_user_id = %s order by requested_on desc limit 10 offset %s", [accountID, page])
        getSent = 0
    else:
        cursor = execute_sql("select null from friend_requests where user_id = %s", [accountID])
        req_count = cursor.rowcount
        cursor = execute_sql("select id,req_user_id,comment,requested_on,is_new from friend_requests where user_id = %s order by requested_on desc limit 10 offset %s", [accountID, page])
        getSent = 1
    if req_count == 0: return "-2"
    friend_requests = cursor.fetchall()
    friend_string = ""
    for req in friend_requests:
        cursor = execute_sql("select name,icon,color1,color2,icon_type,special from accounts where id = %s", [req[1]])
        user_infos = cursor.fetchall()[0]
        is_new = req[4]
        if is_new == 1:
            is_new = 0
        else:
            is_new = 1
        friend_string = f"{friend_string}1:{user_infos[0]}:2:{req[1]}:9:{user_infos[1]}:10:{user_infos[2]}:11:{user_infos[3]}:14:{user_infos[4]}:15:{user_infos[5]}:16:{req[1]}:32:{req[0]}:35:{req[2]}:41:{req[4]}:37:{req[3]}|"
        if getSent == 0:
            cursor = execute_sql("update friend_requests set is_new = 0 where user_id = %s and req_user_id = %s", [req[1], accountID])
    return f"{friend_string}#{req_count}:{page}:10"

@app.route(f"{flask_path}/acceptGJFriendRequest20.php", methods=["POST"])
async def acceptFriendRequest():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    targetAccountID = request.values.get("targetAccountID")
    requestID = request.values.get("requestID")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("select null from friend_requests where id = %s and user_id = %s and req_user_id = %s", [requestID, targetAccountID, accountID])
    if cursor.rowcount == 0: return "-1"
    cursor = execute_sql("select null from friends where friend1 = %s and friend2 = %s or friend1 = %s and friend2 = %s", [accountID, targetAccountID, targetAccountID, accountID])
    if cursor.rowcount == 0:
        cursor = execute_sql("insert into friends (friend1,friend2) values (%s,%s)", [accountID, targetAccountID])
    cursor = execute_sql("delete from friend_requests where id = %s", [requestID])
    return "1"

@app.route(f"{flask_path}/deleteGJFriendRequests20.php", methods=["POST"])
async def deleteFriendRequest():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    targetAccountID = request.values.get("targetAccountID")
    isSender = int(request.values.get("isSender"))
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    if isSender == 1:
        cursor = execute_sql("delete from friend_requests where user_id = %s and req_user_id = %s", [accountID, targetAccountID])
    else:
        cursor = execute_sql("delete from friend_requests where user_id = %s and req_user_id = %s", [targetAccountID, accountID])
    return "1"

@app.route(f"{flask_path}/removeGJFriend20.php", methods=["POST"])
async def removeFriend():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    targetAccountID = request.values.get("targetAccountID")
    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"
    print(request.values)
    cursor = execute_sql("delete from friends where friend1 = %s and friend2 = %s or friend1 = %s and friend2 = %s", [accountID, targetAccountID, targetAccountID, accountID])
    return "1"

@app.route(f"{flask_path}/getGJRewards.php", methods=["POST"])
async def getChestReward():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    rewardType = request.values.get("rewardType")
    chk = request.values.get("chk")
    udid = request.values.get("udid")

    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    chk = xor_cipher(b64_decode(chk[5:]), "59182")
    cursor = execute_sql("select chest_s_time, chest_b_time, chest_s_count, chest_b_count from accounts where id = %s", [accountID])
    chests_infos = cursor.fetchall()[0]
    small_chest_time = chests_infos[0]
    big_chest_time = chests_infos[1]
    small_chest_count = chests_infos[2]
    big_chest_count = chests_infos[3]
    current_time = int(time.time())
    small_chest_wait = 3600
    big_chest_wait = 14400

    small_chest_str = f"{random.randint(200, 400)},{random.randint(2, 10)},{random.randint(1, 6)},{random.randint(1, 6)}"
    big_chest_str = f"{random.randint(2000, 4000)},{random.randint(20, 100)},{random.randint(1, 6)},{random.randint(1, 6)}"

    small_chest_time_left = small_chest_time - current_time
    big_chest_time_left = big_chest_time - current_time

    match rewardType:
        case "1":
            if small_chest_time > current_time:
                return "-1"
            small_chest_count += 1
            small_chest_time_left = small_chest_wait
            cursor = execute_sql("update accounts set chest_s_count = chest_s_count + 1, chest_s_time = %s where id = %s", [current_time + small_chest_wait, accountID])
        case "2":
            if big_chest_time > current_time:
                return "-1"
            big_chest_count += 1
            big_chest_time_left = big_chest_wait
            cursor = execute_sql("update accounts set chest_b_count = chest_b_count + 1, chest_b_time = %s where id = %s", [current_time + big_chest_wait, accountID])

    if small_chest_time_left < 0:
        small_chest_time_left = 0
    if big_chest_time_left < 0:
        big_chest_time_left = 0

    chest_response = b64_encode(xor_cipher(f"1:{accountID}:{chk}:{udid}:{accountID}:{abs(small_chest_time_left)}:{small_chest_str}:{small_chest_count}:{abs(big_chest_time_left)}:{big_chest_str}:{big_chest_count}:{rewardType}", "59182")).replace("/", "_").replace("+", "-")
    response_hash = chest_response + "pC26fpYaQCtg"
    response_hash = sha1(response_hash.encode()).hexdigest()
    return f"SaKuJ{chest_response}|{response_hash}"

@app.route(f"{flask_path}/getGJMapPacks21.php", methods=["POST"])
async def getMapPacks():
    page = request.values.get("page")
    page = int(page)*10

    cursor = execute_sql("select id,name,levels,stars,coins,difficulty,color from map_packs order by id asc limit 10 offset %s", [page])
    if cursor.rowcount == 0: return "-1"
    pack_data = cursor.fetchall()

    pack_str = ""
    pack_ids = []
    for pack in pack_data:
        pack_ids.append(pack[0])
        pack_str = f"{pack_str}1:{pack[0]}:2:{pack[1]}:3:{pack[2]}:4:{pack[3]}:5:{pack[4]}:6:{pack[5]}:7:{pack[6]}:8:{pack[6]}|"

    cursor = execute_sql("select null from map_packs")
    pack_count = cursor.rowcount
    pack_str = pack_str[:-1]

    pack_lvl_hash = get_mappacks_hash(pack_ids)

    response = f"{pack_str}#{pack_count}:{page}:10#{pack_lvl_hash}"
    return response

@app.route(f"{flask_path}/getGJChallenges.php", methods=["POST"])
async def getQuests():
    accountID = request.values.get("accountID")
    gjp = request.values.get("gjp")
    udid = request.values.get("udid")
    chk = request.values.get("chk")
    chk = xor_cipher(b64_decode(chk[5:]), "19847")

    gjp_check = check_gjp(accountID, gjp)
    if not gjp_check:
        return "-1"

    cursor = execute_sql("select id,name,type,amount,reward from quests")
    if cursor.rowcount < 3:
        return "-1"
    quests = cursor.fetchall()

    quest1 = random.choice(quests)
    quests.remove(quest1)
    quest2 = random.choice(quests)
    quests.remove(quest2)
    quest3 = random.choice(quests)

    quest1_resp = f"{quest1[0]},{quest1[2]},{quest1[3]},{quest1[4]},{quest1[1]}"
    quest2_resp = f"{quest2[0]},{quest2[2]},{quest2[3]},{quest2[4]},{quest2[1]}"
    quest3_resp = f"{quest3[0]},{quest3[2]},{quest3[3]},{quest3[4]},{quest3[1]}"

    current_time = int(time.time())
    next_midnight = ((current_time//86400)+1)*86400

    response = b64_encode(xor_cipher(f"SaKuJ:{accountID}:{chk}:{udid}:{accountID}:{next_midnight-current_time}:{quest1_resp}:{quest2_resp}:{quest3_resp}", "19847"))
    hashed = sha1((response + "oC36fpYaPtdg").encode()).hexdigest()
    return f"SaKuJ{response}|{hashed}"

@app.route("/test", methods=["POST", "GET"])
async def test():
    return "k"

def get_demon_rate_name(rate_id, type = None):
    rate_id = int(rate_id)
    demon_name = "Unknown"
    if type == "real":
        if rate_id == 3:
            demon_name = "Easy"
        elif rate_id == 4:
            demon_name = "Medium"
        elif rate_id == 0:
            demon_name = "Hard"
        elif rate_id == 5:
            demon_name = "Insane"
        elif rate_id == 6:
            demon_name = "Extreme"
    else:
        if rate_id == 1:
            demon_name = "Easy"
        elif rate_id == 2:
            demon_name = "Medium"
        elif rate_id == 3:
            demon_name = "Hard"
        elif rate_id == 4:
            demon_name = "Insane"
        elif rate_id == 5:
            demon_name = "Extreme"
    return demon_name

def start_cron():
    while True:
        print("Started cron")
        cursor = execute_sql("select verified,id,created_on from accounts")
        all_users = cursor.fetchall()
        for user in all_users:
            is_verified = user[0]
            user_id = user[1]
            created_on = user[2]
            # Delete account if its not verified after 15 minutes
            if is_verified == 0:
                current_timestamp = int(time.time())
                if created_on+900 < current_timestamp:
                    cursor = execute_sql("select ip from accounts where id = %s", [user_id])
                    ip = cursor.fetchall()[0][0]
                    cursor = execute_sql("delete from accounts where id = %s", [user_id])
                    if ip != "127.0.0.1":
                        cursor = execute_sql("delete from register_ips where ip = %s", [ip])
                continue
            # Set creator points of all users
            cursor = execute_sql("select stars,featured,epic from levels where author_id = %s", [user_id])
            all_levels = cursor.fetchall()
            cp = 0
            for level in all_levels:
                if level[0] > 0:
                    cp += 1
                if level[1] == 1:
                    cp += 1
                if level[2] > 0:
                    cp += 1
            cursor = execute_sql("update accounts set creator_points = %s where id = %s", [cp, user_id])
        print("Finished cron")
        time.sleep(300)

def xor_cipher(string: str, key: str) -> str:
    return ("").join(chr(ord(x) ^ ord(y)) for x, y in zip(string, itertools.cycle(key)))

def b64_encode(string):
    string = string.encode("ascii")
    return base64.b64encode(string).decode()

def b64_decode(string):
    string = string.encode("ascii")
    return base64.b64decode(string).decode()

def get_gjp(password):
    password = xor_cipher(password, "37526")
    password = b64_encode(password)
    return str(password).replace("/", "_").replace("+", "-")

def check_gjp(user_id, given_gjp):
    cursor = execute_sql("select password from accounts where id = %s and verified = 1", [user_id])
    if cursor.rowcount == 0:
        return False
    encrypted_password = cursor.fetchall()[0][0]
    cipher_suite = Fernet(encryption_key)
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
    gjp = get_gjp(decrypted_password)
    if gjp != given_gjp:
        return False
    else:
        return True

def get_user_name(id):
    cursor = execute_sql("select name from accounts where id = %s", [id])
    if cursor.rowcount > 0:
        name = cursor.fetchall()[0][0]
    else:
        name = None
    return name

def get_levels_hash(lvl_list):
    hash = ""
    for id in lvl_list:
        cursor = execute_sql("SELECT id, stars, coins_verified FROM levels WHERE id = %s", [id])
        level = cursor.fetchall()[0]
        hash = f"{hash}{str(level[0])[0]}{str(level[0])[len(str(level[0]))-1]}{str(level[1])}{str(level[2])}"
    hash = hash + "xI25fpAapCQg"
    encoded = sha1(hash.encode())
    return encoded.hexdigest()

def get_encode_song(song_id):
    cursor = execute_sql("SELECT id,name,author_id,author_name,size,download_link FROM songs WHERE id = %s LIMIT 1", [song_id])
    if cursor.rowcount == 0:
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-Agent": ""}
        data = {"songID": song_id,
                "secret": "Wmfd2893gb7"}
        req = requests.post("http://www.boomlings.com/database/getGJSongInfo.php", data=data, headers=headers)
        response = req.text
        if response == "-2":
            return response
        elif response == "-1":
            return response
        resp = response.replace("~", "").split("|")
        cursor = execute_sql("insert into songs (id,name,author_id,author_name,size,download_link) values (%s,%s,%s,%s,%s,%s)", [resp[1], resp[3], resp[5], resp[7], resp[9], resp[13]])
        return req.text
    elif cursor.rowcount == 1:
        song_info = cursor.fetchall()[0]
        song_name = song_info[1].replace("#", "")
        return f"1~|~{song_info[0]}~|~2~|~{song_name}~|~3~|~{song_info[2]}~|~4~|~{song_info[3]}~|~5~|~{song_info[4]}~|~6~|~~|~10~|~{song_info[5]}~|~7~|~~|~8~|~1"

def get_encoded_lvlstring(lvlstring):
    lvl_hash = []
    length = len(lvlstring)
    divided = int(length/40)
    count = 0
    kcount = 0
    first_loop = False
    while True:
        if kcount < length:
            if first_loop == True:
                kcount = kcount+divided
                if count > 39:
                    break
            lvl_hash.append(lvlstring[kcount])
            count += 1
        else:
            break
        first_loop = True
    lvl_hash = "".join(lvl_hash)
    print(lvl_hash)
    lvl_hash = lvl_hash + "xI25fpAapCQg"
    encoded = sha1(lvl_hash.encode())
    return encoded.hexdigest()

def get_mappacks_hash(lvl_list):
    hash = ""
    for lvl_id in lvl_list:
        cursor = execute_sql("select id,stars,coins from map_packs where id = %s", [lvl_id])
        pack_info = cursor.fetchall()[0]
        hash = f"{hash}{str(pack_info[0])[0]}{str(pack_info[0])[len(str(pack_info[0]))-1]}{pack_info[1]}{pack_info[2]}"
    hash = hash + "xI25fpAapCQg"
    return sha1(hash.encode()).hexdigest()

def send_mail(send_to, content):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Account verification"
    message["From"] = f"Ultimate GDPS <{mail_email}>"
    message["To"] = send_to
    message["Date"] = formatdate(localtime=True)
    part1 = MIMEText(content, "html")
    message.attach(part1)

    smtpObj = smtplib.SMTP(mail_smtp_server, mail_port)
    smtpObj.starttls()
    smtpObj.login(mail_email, mail_password)
    smtpObj.sendmail(mail_email, send_to, message.as_string())  

def generate_token():
    characters = list(string.ascii_letters + string.digits)
    random.shuffle(characters)
    password = []
    for i in range(60):
        password.append(random.choice(characters))
    random.shuffle(password)
    return "".join(password)

def execute_sql(command, values=None):
    global cursor
    try:
        cursor.execute(command, values)
    except Exception as e:
        print(e)
        global connection
        connection.disconnect()
        count = 0
        while True:
            connection = mysql.connector.connect(host=mysql_ip,
                                                database=mysql_database,
                                                user=mysql_user,
                                                port = int(mysql_port),
                                                password=mysql_pass)
            if connection.is_connected:
                cursor = connection.cursor(buffered=True)
                connection.autocommit = 1
                try:
                    cursor.execute(command, values)
                except Exception as e:
                    count += 1
                    if count == 5:
                        return None
                    print(e)
                    asyncio.sleep(5)
                    continue
                return cursor
            else:
                asyncio.sleep(5)
    return cursor

if __name__ == "__main__":
    if in_production == "true":
        threading.Thread(target=start_cron, daemon=True).start()
        from waitress import serve
        serve(app, host=host, port=port)
    else:
        app.run(host=host, port=port)