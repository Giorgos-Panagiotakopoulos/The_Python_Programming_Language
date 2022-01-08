import sys
from datetime import datetime

# WEIGHTED

import matplotlib.pyplot as plt
import mysql.connector
import numpy as np
import pandas as pd
import seaborn as sns
import isodate
from pyyoutube import Api
from sklearn import preprocessing
from sqlalchemy import create_engine
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from youtube_transcript_api import YouTubeTranscriptApi
from youtubesearchpython import Search
from apscheduler.schedulers.blocking import BlockingScheduler

# Ορίζουμε εδώ τις παραμέτρους σύνδεσης με τη βάση δεδομένων MySQL
db_host = "localhost"
db_user = "root"
db_password = ""
db_database = "youtubeproject"

playlistVideoLimit = 100

# arguments to be passed to build function
# kets AIzaSyCBTgHHl1MfdrvS5qzv7tEkyfMg0EX_hiE
# keys AIzaSyBTDffOqjyNvbEKxBEyryf6kCKfji9lS58
# keys AIzaSyB8QQP16j4Pzt1l8m7b_Cso1lwCqg1tA4I
DEVELOPER_KEY = "AIzaSyB8QQP16j4Pzt1l8m7b_Cso1lwCqg1tA4I"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# creating youtube resource object
# for interacting with API
# youtube = build(YOUTUBE_API_SERVICE_NAME,
#                YOUTUBE_API_VERSION,
#                developerKey=DEVELOPER_KEY)

api = Api(api_key=DEVELOPER_KEY)


def menu() :
    print('|-------------- YOUTUBE PROJECT-----------------|')
    print('|                                               |')
    print('| 1.  New video search                          |')
    print('| 2.  Update video data                         |')
    print('| 3.  Index analysis                            |')
    print('| 4.  Get Video Trends                          |')
    print('|                                               |')
    print('| 0.  Exit                                      |')
    print('|-----------------------------------------------|')
    return input('Your choice: ')


def processPlaylistVideo(video_id) :
    print("Processing " + str(video_id))
    video_res = api.get_video_by_id(video_id=video_id)
    try :
        item = video_res.items[0]
    except :
        return np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN

    # To λεξικό προστίθεται σε μία λίστα, η οποία περιλαμβάνει τελικά
    # όλα τα λεξικά με τα απαραίτητα 4 στοιχεία των βίντεο της playlist
    if checkTerms(keywords, item.snippet.title) == True and \
            checkEpisodes(item.snippet.title) == False :
        return item.id, \
               item.kind, \
               item.snippet.title, \
               "https://www.youtube.com/watch?v=" + item.id, \
               isodate.parse_duration(item.contentDetails.duration).seconds, \
               item.statistics.viewCount, \
               item.statistics.likeCount, \
               item.statistics.dislikeCount
    else :
        return np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN


def processVideo(video_id) :
    print("Processing " + str(video_id))
    video_res = api.get_video_by_id(video_id=video_id)
    try :
        item = video_res.items[0]
    except :
        return np.NAN, np.NAN, np.NAN, np.NAN

    # To λεξικό προστίθεται σε μία λίστα, η οποία περιλαμβάνει τελικά
    # όλα τα λεξικά με τα απαραίτητα 4 στοιχεία των βίντεο της playlist
    if checkTerms(keywords, item.snippet.title) == True and \
            checkEpisodes(item.snippet.title) == False :
        return isodate.parse_duration(item.contentDetails.duration).seconds, \
               item.statistics.viewCount, \
               item.statistics.likeCount, \
               item.statistics.dislikeCount
    else :
        return np.NAN, np.NAN, np.NAN, np.NAN


def processPlaylist(playlist_id) :
    print("Processing list: " + str(playlist_id))
    playlist_item_result = api.get_playlist_items(playlist_id=playlist_id, count=120)
    playlist_item_result_df = pd.DataFrame(playlist_item_result.items)
    playlist_item_result_df['id'], playlist_item_result_df['type'], playlist_item_result_df['title'], \
    playlist_item_result_df['link'], playlist_item_result_df['Duration'], playlist_item_result_df['View_Count'], \
    playlist_item_result_df['Likes'], playlist_item_result_df['Dislikes'] = \
        zip(*playlist_item_result_df['contentDetails'].apply(
            lambda contentDetails : processPlaylistVideo(contentDetails['videoId'])))

    playlist_item_result_df = playlist_item_result_df.dropna()
    playlist_item_result_df = playlist_item_result_df[
        ['id', 'type', 'title', 'link', 'Duration', 'View_Count', 'Likes', 'Dislikes']]
    # drop if duplicated videos exists in playlist
    return playlist_item_result_df[
        ~playlist_item_result_df.index.duplicated(keep='first')]  # playlist_item_result_df.head(100)


def cleanSubText(subtitle) :
    subtitle = subtitle.replace('[', '(')
    subtitle = subtitle.replace(']', ')')
    subtitle = subtitle.replace('♪', '')
    subtitle = subtitle.replace("\n", ' ')
    subtitle = ' '.join(subtitle.split())
    leftParenthesisPosition = subtitle.find('(')
    allString = subtitle
    while leftParenthesisPosition >= 0 :
        leftParenthesisPosition = allString.find('(')
        rightParenthesisPosition = allString.find(')')
        if leftParenthesisPosition >= 0 :
            leftSubstr = allString[:leftParenthesisPosition]
            rightSubstr = allString[rightParenthesisPosition + 1 :]
            allString = leftSubstr + rightSubstr
    allString = allString.strip()
    return allString


# H def checkTerms, γράφτηκε για να ελέγχει εάν τουλάχιστον
# ΜΙΑ από τις λέξεις που αναζητούμε βρίσκεται μέσα στον
# τίτλο του video που επέστρεψε η αναζήτηση του YouTube.
# Δέχεται δύο ορίσματα (arguments):
# 1. terms: στην ουσία το πρώτο όρισμα είναι το string το οποίο αναζητήσαμε στο YouTube
#           πχ. "mickey mouse cartoon english subtitles"
# 2. title: πρόκειται για τον εκάστοτε τίτλο του video που επέστρεψε η αναζήτησ
#          στο YouTube. Επειδή η αναζήτηση επιστρέφει πολλά video, πρέπει να ελέγχω
#          το καθένα απ' αυτα, ώστε να διαπιστώνω εάν έχει μία τουλάχιστον από τις
#          λέξεις αναζήτησης στον τίτλο του.

def checkTerms(terms, title) :
    # mickey mouse cartoon english subtitles
    terms_list = terms.split()
    # H terms_list θα έχει τη μορφή:
    # ['mickey', 'mouse', 'cartoon', 'english', 'subtitles']
    # Ο μετρητής match_count αυξάνεται κάθε φορά που ένα στοιχείο της λίστας terms_list
    # εντοπίζεται μέσα στο string με όνομα title (2o όρισμα της def)
    match_count = 0
    # Για κάθε στοιχείο (λέξη) που υπάρχει μέσα στη λίστα terms_list
    # η def ψάχνει να βρει εάν αυτή υπάρχει στο string title (που στην ουσία είναι ο τίτλος του βίντεο)
    for term in terms_list :
        # Χρησιμοποιώ τη μέθοδο .upper() για να μετατρέψω τόσο τον όρο αναζήτησης (term)
        # όσο και τον τίτλο του video (title) σε κεφαλαίους χαρακτήρες,
        # ώστε η εύρεση του όρου μέσα στον τίτλο να μην εξαρτάται από το εάν ο
        # όρος αναζήτησης και ο τίτλος είναι γραμμένος με κεφαλαία ή μικρά ή μείγμα αυτών.
        if title.upper().find(term.upper()) >= 0 :
            # Εάν βρεθεί ταίριασμα, αυξάνω τον μετρητή που μετρά τα ταιριάσματα
            # και διακόπτει τη λειτουργία της def, επιστρέφοντας τη λογική τιμή True.
            # Αυτό γίνεται για να εξοικονομείται χρόνος επεξεργασίας, αφού δε χρειάζεται
            # να ψάξω εάν υπάρχει και άλλος όρος στον τίτλο, αφού βρήκα τουλάχιστον ένα,
            # οπότε το κριτήριο πληρείται.
            match_count = match_count + 1
            return True
    # Εάν ο μετρητής match_count δεν αυξήθηκε για κανέναν όρο της terms_list, αυτό σημαίνει ότι
    # κανένας όρος αναζήτησης δεν βρέθηκε μέσα στον τίτλο του βίντεο.
    # H def θα επιστρέψει στο πρόγραμμα τη λογική τιμή False, για να δείξει
    # ότι κανείς όρος αναζήτησης δεν υπάρχει στον τίτλο που πέρασε σαν 2ο όρισμα
    if match_count == 0 :
        return False


def checkEpisodes(title) :
    terms = "Episodes compilation"
    terms_list = terms.split()
    # Ο μετρητής match_count αυξάνεται κάθε φορά που ένα στοιχείο της λίστας terms_list
    # εντοπίζεται μέσα στο string με όνομα title (2o όρισμα της def)
    match_count = 0
    # Για κάθε στοιχείο (λέξη) που υπάρχει μέσα στη λίστα terms_list
    # η def ψάχνει να βρει εάν αυτή υπάρχει στο string title (που στην ουσία είναι ο τίτλος του βίντεο)
    for term in terms_list :
        # Χρησιμοποιώ τη μέθοδο .upper() για να μετατρέψω τόσο τον όρο αναζήτησης (term)
        # όσο και τον τίτλο του video (title) σε κεφαλαίους χαρακτήρες,
        # ώστε η εύρεση του όρου μέσα στον τίτλο να μην εξαρτάται από το εάν ο
        # όρος αναζήτησης και ο τίτλος είναι γραμμένος με κεφαλαία ή μικρά ή μείγμα αυτών.
        if title.upper().find(term.upper()) >= 0 :
            # Εάν βρεθεί ταίριασμα, αυξάνω τον μετρητή που μετρά τα ταιριάσματα
            # και διακόπτει τη λειτουργία της def, επιστρέφοντας τη λογική τιμή True.
            # Αυτό γίνεται για να εξοικονομείται χρόνος επεξεργασίας, αφού δε χρειάζεται
            # να ψάξω εάν υπάρχει και άλλος όρος στον τίτλο, αφού βρήκα τουλάχιστον ένα,
            # οπότε το κριτήριο πληρείται.
            match_count = match_count + 1
            return True
    # Εάν ο μετρητής match_count δεν αυξήθηκε για κανέναν όρο της terms_list, αυτό σημαίνει ότι
    # κανένας όρος αναζήτησης δεν βρέθηκε μέσα στον τίτλο του βίντεο.
    # H def θα επιστρέψει στο πρόγραμμα τη λογική τιμή False, για να δείξει
    # ότι κανείς όρος αναζήτησης δεν υπάρχει στον τίτλο που πέρασε σαν 2ο όρισμα
    if match_count == 0 :
        return False


def evaluateContent(video_id) :
    try :
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list :
            if transcript.language_code == 'en' :
                # get subs DF
                subs_df = pd.DataFrame(transcript.fetch())
                # filter subs
                subs_df["text"] = subs_df['text'].apply(cleanSubText)
                # get all subtitles as a string
                subtitles = " ".join(subs_df.text.tolist())
                # filter subs
                subtitles = cleanSubText(subtitles)
                print('Analyzing ' + subtitles + '...')
                polarity = TextBlob(subtitles).polarity
                blob_object = TextBlob(subtitles, analyzer=NaiveBayesAnalyzer())
                # Running sentiment analysis
                analysis = blob_object.sentiment
                p_pos = analysis[1]
                p_neg = analysis[2]
                naive_polarity = p_pos - p_neg

                # return tous 5 diktes pou ipologisame apo tous 2 analites
                return round(polarity, 4), round(normalize(polarity), 4), round(naive_polarity, 4), round(normalize(naive_polarity), 4),\
                       round(((normalize(polarity)*1.5) + (normalize(naive_polarity)*0.5)) / 2, 4), True
            else :
                # else if no eng subs return 5 nan kai to flag an einai to content valid = false
                print("DEN EXEI AGGLIKA TO VIDEO: {}".format(format(video_id)))
                return np.nan, np.nan, np.nan, np.nan, np.nan, False

    except Exception :
            # else if exception occured (ex den exei subtitles) return 5 nan kai to flag an einai to content valid = false
            print("Subtitles are disabled for this video: {}".format(format(video_id)))
            return np.nan, np.nan, np.nan, np.nan, np.nan, False


def normalize(x) :
    y = (x + 1) / 2
    return y


def update_data() :
    # Κρατάει το χρόνο έναρξης της διαδικασίας ενημέρωσης των video
    start_time = datetime.now()
    mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )

    dbcursor = mydb.cursor()
    dbcursor.execute("SELECT IFNULL(max(run_id)+1, 1) FROM runs")
    dbresult = dbcursor.fetchall()
    for row in dbresult :
        run_id = row[0]

    dbcursor = mydb.cursor()
    dbcursor.execute("SELECT id FROM videos")
    dbresult = dbcursor.fetchall()

    for row in dbresult :
        video_index = row[0]
        video_data = api.get_video_by_id(video_id=video_index)
        video_data = video_data.to_dict()
        video_data = video_data['items']
        for item in video_data :
            viewCount = item['statistics']['viewCount']
            likeCount = item['statistics']['likeCount']
            dislikeCount = item['statistics']['dislikeCount']

            mycursor = mydb.cursor()
            sql = "INSERT INTO runs (run_id, video_id, view_count, likes, dislikes) VALUES (%s, %s, %s, %s, %s)"
            val = (run_id, video_index, viewCount, likeCount, dislikeCount)
            mycursor.execute(sql, val)
            mydb.commit()
    # Κρατάει το χρόνο ολοκλήρωσης της διαδικασίας ενημέρωσης των video
    end_time = datetime.now()
    # Υπολογισμός της διαφοράς των δύο χρόνων για να προκύψει ο χρόνος εκτέλεσης
    execution_time = end_time - start_time
    # Μετατρέπει το αποτέλεσμα σε δευτερόλεπτα
    time_in_seconds = execution_time.total_seconds()
    # Αποθηκεύει το αποτέλεσμα στον πίνακα benchmarks
    sql = "INSERT INTO benchmarks (run_id, run_duration) VALUES (%s, %s)"
    val = (run_id, time_in_seconds)
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()


def some_job() :
    print("Decorated job")


def get_trends_job() :
    scheduler = BlockingScheduler()
    scheduler.add_job(update_data, 'interval', hours=1, start_date='2021-01-21 00:20:00',
                      end_date='2021-01-23 00:20:00')
    scheduler.start()


# Ρυθμίζουμε το Pandas ώστε να εκτυπώνει όλες τις γραμμές
# και όλες τις στήλες των dataframes
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

choice = 0

# Ελέγχει εάν η εφαρμογή τρέχει με command line argument -u
# Εάν υπάρχει argument -u, τότε ενημερώνει τα στοιχεία των video που έχουν καταχωρηθεί
# στον πίνακα video
# Διαφορετικά, η εφαρμογή τρέχει με το μενού.
if len(sys.argv) > 1 :
    if sys.argv[1] == '-u' :
        update_data()
else :
    while choice not in ['1', '2', '3', '4', '0'] :
        choice = menu()

    # Repeat reading user's choice, until he/she types 0 to exit the program
    if choice == '1' :
        # mickey mouse cartoon english subtitles
        # Ζητάμε τους όρους αναζήτησης από το χρήστη
        keywords = input('Search terms: ')
        # keywords = "mickey mouse cartoon english subtitles"
        # Ζητάμε το πλήθος των αποτελεσμάτων που θέλουμε
        # να επιστρέψει η αναζήτηση στο YouTube
        # limit = int(input('How many results: '))
        limit = 300

        # Κρατάει το χρόνο έναρξης της διαδικασίας ενημέρωσης των video
        start_time = datetime.now()

        # Καλούμε τη συνάρτηση Search απ' τη βιβλιοθήκη youtubesearchpython
        # Δέχεται 2 ορίσματα:
        # 1. Το string keywords, το οποίο περιέχει τις λέξεις που έδωσε ο χρήστης
        #    και θέλει να αναζητήσει στο YouTube
        # 2. Το μέγιστο πλήθος αποτελεσμάτων που ο χρήστης θέλει να λάβει από το YouTube
        youTubeResults = Search(keywords, limit=limit)
        # H Search επιστρέφει ένα Python dictionary,
        # στο οποίο δίνουμε το όνομα resultVideos

        resultVideos = youTubeResults.result()

        # Από το dictionary που επέστρεψε η μέθοδος .result()
        # κρατάμε μόνο το key 'result', το οποίο περιέχει
        # τις χρήσιμες πληροφορίες του κάθε βίντεο
        resultVideos = resultVideos['result']

        # Δημιουργία dataframe με τα στοιχεία των video
        # που επέστρεψε η μέθοδος Search με όρισμα
        # ta keywords αναζήτησης που έδωσε ο χρήστης.
        videos = pd.DataFrame(resultVideos)
        for i in range(1, 10) :  # 10
            print(
                '*******************************************************************************************************')
            youTubeResults.next()
            nextPageData = youTubeResults.result()
            nextPageData = nextPageData['result']
            nextPageDataDF = pd.DataFrame(nextPageData)
            videos = videos.append(nextPageDataDF)
        # Από το συνολικό dataframe το οποίο περιέχει 13 στήλες,
        # κρατάμε μόνο τις 4 χρήσιμες στήλες: 'id', 'type', 'title', 'link'
        videos = videos[['id', 'type', 'title', 'link']]
        # Διαγράφει τυχόν διπλότυπα video
        # videos = videos.drop_duplicates(subset='id', keep="first")
        videos.set_index('id', inplace=True)
        videos = videos[~videos.index.duplicated(keep='first')]
        print('=============== VIDEOS =================================================')
        # videos = videos.head(110)

        ## XORIZOUME TA RESULTS APO TIN ANAZITISI STA 2
        ## 1) KRATAME TIN LISTA ME TA APOTELESMATA XORIS TIS PLAYLIST (to df auto exei index to id)
        ## 2) KRATAME MIA LISTA MONO ME TIS PLAYLIST
        playlists = videos[videos['type'] == 'playlist']
        videos.drop(videos[videos["type"] == "playlist"].index, inplace=True)

        ## EPE3ERGAZOMASTE TIS PLAYLIST
        # playlist_videos["videos"] = playlist_videos.apply(lambda row : processPlaylist(row.index))
        playlist_videos = []
        for index, row in playlists.iterrows() :
            pl_vids = processPlaylist(index)
            pl_vids['playlist_id'] = index
            playlist_videos.append(pl_vids)

        playlist_videos = pd.concat(playlist_videos, axis=0)
        ## MAKE ID AS INDEX AND DROP DUPLICATES
        playlist_videos.set_index('id', inplace=True)
        playlist_videos = playlist_videos[~playlist_videos.index.duplicated(keep='first')]

        ## PREPROCESS INITIAL LIST RESULTS (INITIAL VIDEOS)
        videos['Duration'], videos['View_Count'], \
        videos['Likes'], videos['Dislikes'] = \
            zip(*videos.apply(
                lambda row : processVideo(row.name), axis=1))
        ## filter results:
        ## 1) drop NaN
        ## 2) keep 100 first results
        videos = videos.dropna()
        # videos = videos.head(100) ## TODO CHECK IF THIS MUST BE DONE NOW

        ## FILTRAROUME KAI TA ARXIKA VIDEO KAI TA VIDEO APO TIS LISTES VASI TO DURATION
        meanDuration = (videos.Duration.mean() + playlist_videos.Duration.mean()) / 2
        videos = videos[videos["Duration"] <= 2 * meanDuration]
        playlist_videos = playlist_videos[playlist_videos["Duration"] <= 2 * meanDuration]

        ## EKSAGOUME TOUS YPOTITLOUS KAI TO SINESTIMATIKO PERIEXOMENO.
        videos['polarity_Pattern'], videos['polarity_Pattern_Norm'], videos['polarity_Naive'], \
        videos['polarity_Naive_Norm'], videos['polarity_composite'], videos['isContentValid'] = zip(*videos.apply(
            lambda row : evaluateContent(row.name), axis=1))

        playlist_videos['polarity_Pattern'], playlist_videos['polarity_Pattern_Norm'], playlist_videos['polarity_Naive'], \
        playlist_videos['polarity_Naive_Norm'], playlist_videos['polarity_composite'], playlist_videos['isContentValid'] = zip(*playlist_videos.apply(
            lambda row : evaluateContent(row.name), axis=1))

        ## clean NLP RESULTS!
        ## 1) REMOVE VIDEOS WITH FALSE IS VALID CONTENT FLAG (to isValid content false an to video den exei agglikous ipotitlous)
        ## 2) drop videos with nan diktes an iparxoun
        videos = videos[videos['isContentValid']].dropna()
        playlist_videos = playlist_videos[playlist_videos['isContentValid']].dropna()

        # convert view count like and dislike to int
        videos['View_Count'] = videos['View_Count'].astype(int)
        videos['Likes'] = videos['Likes'].astype(int)
        videos['Dislikes'] = videos['Dislikes'].astype(int)
        playlist_videos['View_Count'] = playlist_videos['View_Count'].astype(int)
        playlist_videos['Likes'] = playlist_videos['Likes'].astype(int)
        playlist_videos['Dislikes'] = playlist_videos['Dislikes'].astype(int)

        # reset indexes
        videos.reset_index(inplace=True)
        playlist_videos.reset_index(inplace=True)

        # ipologizoume ena neo column like/dislike rate
        videos['like/dislike rate'] = videos.apply(lambda row : 0 if (row['Likes'] + row['Dislikes']) == 0 else row['Likes'] / (row['Likes'] + row['Dislikes']), axis=1)
        playlist_videos['like/dislike rate'] = playlist_videos.apply(lambda row : 0 if (row['Likes'] + row['Dislikes']) == 0 else row['Likes'] / (row['Likes'] + row['Dislikes']) , axis=1)

        like_dislike_rate = (videos['like/dislike rate'].mean() + playlist_videos['like/dislike rate'].mean()) / 2
        views_rate = (videos['View_Count'].mean() + playlist_videos['View_Count'].mean()) / 2


        # get CI from videos that have like_dislike_rate and views_rate greater than te average
        filtered_videos = videos[(videos['like/dislike rate'] >= like_dislike_rate) & (videos['View_Count'] >= views_rate)]
        filtered_playlist_videos = playlist_videos[(playlist_videos['like/dislike rate'] >= like_dislike_rate) & (playlist_videos['View_Count'] >= views_rate)]

        # creates a dataframe of filtered videos
        top_videos_df = filtered_videos.append(filtered_playlist_videos)
        all_videos_df = videos.append(playlist_videos)
        # drop unnecessary values
        top_videos_df.drop(["id", 'playlist_id', 'isContentValid', 'type', 'title', 'link'], axis=1, inplace=True)
        all_videos_df.drop(["id", 'playlist_id', 'isContentValid', 'type', 'title', 'link'], axis=1, inplace=True)

        # extract more CI indexes pirazontas ta varoi
        top_videos_df["new_ci_50/150"] = top_videos_df.apply(
            lambda row : round(((row["polarity_Pattern_Norm"] * 0.50) + (row['polarity_Naive_Norm'] * 1.5)) / 2, 4), axis=1)
        top_videos_df["new_ci_150/50"] = top_videos_df.apply(
            lambda row : round(((row["polarity_Pattern_Norm"] * 1.50) + (row['polarity_Naive_Norm'] * 0.5)) / 2, 4), axis=1)
        all_videos_df["new_ci_50/150"] = all_videos_df.apply(
            lambda row : round(((row["polarity_Pattern_Norm"] * 0.50) + (row['polarity_Naive_Norm'] * 1.5)) / 2, 4), axis=1)
        all_videos_df["new_ci_150/50"] = all_videos_df.apply(
            lambda row : round(((row["polarity_Pattern_Norm"] * 1.50) + (row['polarity_Naive_Norm'] * 0.5)) / 2, 4), axis=1)

        # get correlation of these values
        top_videos_corr = top_videos_df.corr()
        all_videos_corr = all_videos_df.corr()

        # plot correlograms for top_videos and all videos
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(top_videos_corr, square=True, vmin=-1, vmax=1, center=0,
                    cmap=sns.diverging_palette(20, 220, n=200)).set_title("All Data Heatmap")
        plt.show()

        # display corellation of new_ci_150/50
        top_videos_df = top_videos_df.sort_values(['Likes'], ascending=False)
        plt.plot(top_videos_df["Likes"].to_list(),top_videos_df["new_ci_150/50"].to_list(), color="blue", linewidth= 1.5, alpha=0.5)
        plt.xlabel('Likes')
        plt.ylabel('Composite Index')
        plt.title('Composite Index weighted 150% to Pattern And 50% to Naive')
        plt.show()

        sns.heatmap(all_videos_corr, square=True, vmin=-1, vmax=1, center=0,
                    cmap=sns.diverging_palette(20, 220, n=200)).set_title("All Data Heatmap")
        plt.show()

        # get final df
        videos = videos.head(100)

        # get 100 first videos of 3 playlists with most videos
        top_playlist_indexes = playlist_videos["playlist_id"].value_counts().index
        for id in list(top_playlist_indexes)[:3]:
            append_df = playlist_videos[playlist_videos['playlist_id'] == id].head(100)
            videos = videos.append(append_df)

        videos.drop_duplicates(subset=['id'], inplace=True)
        videos.set_index('id', inplace=True)

        # fix dataframe
        videos.drop(['playlist_id', 'isContentValid', 'like/dislike rate'], axis=1, inplace=True)
        # update polarity composite. vazoume ton dikti me ta varoi pros ton pattern analyzer
        # videos["polarity_composite"] = all_videos_df.apply(
        #     lambda row : round(((row["polarity_Pattern_Norm"] * 1.50) + (row['polarity_Naive_Norm'] * 0.5)) / 2, 4),
        #     axis=1)


        sqlEngine = create_engine('mysql+pymysql://root:@127.0.0.1/youtubeproject', pool_recycle=3600)
        conn = sqlEngine.connect()
        try :
            # Πρώτα δημιουργεί τον πίνακα videos στη βάση δεδομένων.
            # Εάν αυτός υπάρχει, τον διαγράφει και τον δημιουργεί εκ νέου
            mydb = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_database
            )

            dbcursor = mydb.cursor()
            sql = "DROP TABLE IF EXISTS videos"
            dbcursor.execute(sql)
            mydb.commit()

            # Δημιουργεί εκ νέου τον πίνακα videos
            sql = "CREATE TABLE videos (" \
                  "video_index bigint(20) DEFAULT NULL, " \
                  "id text DEFAULT NULL, " \
                  "type text DEFAULT NULL, " \
                  "title text DEFAULT NULL, " \
                  "link text DEFAULT NULL, " \
                  "Duration double DEFAULT NULL, " \
                  "view_count bigint(20) DEFAULT NULL, " \
                  "Likes bigint(20) DEFAULT NULL, " \
                  "Dislikes bigint(20) DEFAULT NULL, " \
                  "polarity_Pattern double DEFAULT NULL, " \
                  "polarity_Pattern_Norm double DEFAULT NULL, " \
                  "polarity_Naive double DEFAULT NULL, " \
                  "polarity_Naive_Norm double DEFAULT NULL, " \
                  "polarity_composite double DEFAULT NULL, " \
                  "video_index_p double DEFAULT NULL, " \
                  "video_index_r double DEFAULT NULL, " \
                  "video_index_lpv double DEFAULT NULL, " \
                  "video_index_dpv double DEFAULT NULL, " \
                  "video_index_vpd double DEFAULT NULL)"
            dbcursor.execute(sql)
            mydb.commit()

            # Στη συνέχεια δημιουργεί τον πίνακα runs.
            # Εάν αυτός υπάρχει, πρώτα τον διαγράφει
            dbcursor = mydb.cursor()
            sql = "DROP TABLE IF EXISTS runs"
            dbcursor.execute(sql)
            mydb.commit()

            sql = "CREATE TABLE IF NOT EXISTS runs (" \
                  "run_id int(11) NOT NULL, " \
                  "video_id text NOT NULL, " \
                  "view_count bigint(20) NOT NULL, " \
                  "likes bigint(20) NOT NULL, " \
                  "dislikes bigint(20) NOT NULL, " \
                  "timestamp timestamp NOT NULL DEFAULT current_timestamp() " \
                  ")"
            dbcursor.execute(sql)
            mydb.commit()

            # Κρατάει το χρόνο ολοκλήρωσης της διαδικασίας ενημέρωσης των video
            end_time = datetime.now()
            # Υπολογισμός της διαφοράς των δύο χρόνων για να προκύψει ο χρόνος εκτέλεσης
            execution_time = end_time - start_time
            # Μετατρέπει το αποτέλεσμα σε δευτερόλεπτα
            time_in_seconds = execution_time.total_seconds()
            # Αποθηκεύει το αποτέλεσμα στον πίνακα benchmarks

            dbcursor = mydb.cursor()
            sql = "DROP TABLE IF EXISTS benchmarks"
            dbcursor.execute(sql)
            mydb.commit()

            sql = "CREATE TABLE IF NOT EXISTS benchmarks (run_id INT NOT NULL, run_duration DOUBLE NOT NULL)"
            dbcursor.execute(sql)
            mydb.commit()

            dbcursor = mydb.cursor()
            sql = "INSERT INTO benchmarks (run_id, run_duration) VALUES (%s, %s)"
            # Θέτουμε run_id = 0 για την αρχική εκτέλεση του προγράμματος
            run_id = 0
            val = (run_id, time_in_seconds)
            dbcursor.execute(sql, val)
            mydb.commit()

            dbcursor.close()
            try :
                videos.to_sql('videos', conn, if_exists='append', index=True)
            except :
                print("Proceeding..")
            conn.close()
        except :
            pass

    if choice == '2' :
        update_data()

    if choice == '3' :
        sqlEngine = create_engine('mysql+pymysql://root:@127.0.0.1/youtubeproject', pool_recycle=3600)
        conn = sqlEngine.connect()
        try :
            # Εκτελεί μία SQL SELECT στον πίνακα runs, για να φορτώσε σε dataframe
            # τα αποτελέσματα που έχει καταγράψει το πρόγραμμα
            sql = pd.read_sql_query('SELECT run_id, video_id, runs.view_count, runs.likes, runs.dislikes, duration '
                                    'FROM runs INNER JOIN videos ON runs.video_id = videos.id', conn)
            runs = pd.DataFrame(sql, columns=['run_id', 'video_id', 'view_count', 'likes', 'dislikes', 'duration'])

            mydb = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_database
            )

            dbcursor = mydb.cursor()
            sql = "UPDATE videos INNER JOIN " \
                  "(SELECT video_id, avg(likes)/avg(dislikes) as video_index_p " \
                  "FROM runs " \
                  "GROUP BY video_id) as calc_p " \
                  "ON videos.id = calc_p.video_id " \
                  "SET videos.video_index_p = calc_p.video_index_p"
            dbcursor.execute(sql)
            mydb.commit()

            # Υπολογισμός του δείκτη p και ενημέρωση του πίνακα videos
            sql = "UPDATE videos INNER JOIN " \
                  "(SELECT video_id, 183*avg(view_count)/max(view_count) as video_index_r  " \
                  "FROM runs " \
                  "GROUP BY video_id) as calc_p " \
                  "ON videos.id = calc_p.video_id " \
                  "SET videos.video_index_r = calc_p.video_index_r"
            dbcursor.execute(sql)
            mydb.commit()

            # Υπολογισμός δείκτη LPV
            sql = "UPDATE videos INNER JOIN " \
                  "(SELECT video_id, avg(likes)/avg(view_count) as video_index_lpv " \
                  "FROM runs " \
                  "GROUP BY video_id) as calc_p " \
                  "ON videos.id = calc_p.video_id " \
                  "SET videos.video_index_lpv = calc_p.video_index_lpv"
            dbcursor.execute(sql)
            mydb.commit()

            # Υπολογισμός δείκτη DPV
            sql = "UPDATE videos INNER JOIN " \
                  "(SELECT video_id, avg(dislikes)/avg(view_count) as video_index_dpv " \
                  "FROM runs " \
                  "GROUP BY video_id) as calc_p " \
                  "ON videos.id = calc_p.video_id " \
                  "SET videos.video_index_dpv = calc_p.video_index_dpv"
            dbcursor.execute(sql)
            mydb.commit()

            # Υπολογισμός δείκτη VPD
            sql = "UPDATE videos INNER JOIN " \
                  "(SELECT video_id, avg(view_count)/2 as video_index_vpd " \
                  "FROM runs " \
                  "GROUP BY video_id) as calc_p " \
                  "ON videos.id = calc_p.video_id " \
                  "SET videos.video_index_vpd = calc_p.video_index_vpd"
            dbcursor.execute(sql)
            mydb.commit()

            conn.close()
        except :
            pass

        # Υπολογισμός των video με τα τρία μεγαλύτερα και τα τρία μικρότερα ci
        sqlEngine = create_engine('mysql+pymysql://root:@127.0.0.1/youtubeproject', pool_recycle=3600)
        conn = sqlEngine.connect()
        try :
            # Εκτελεί μία SQL SELECT στον πίνακα runs, για να φορτώσει σε dataframe
            # τα αποτελέσματα που έχει καταγράψει το πρόγραμμα.
            # Εδώ φορτώνει τα video_id και τους αντίστοιχους δείκτες ci για τα video με τους 3 καλύτερους δείκτες ci
            # και τους 3 χειρότερους δείκτες ci
            sql = 'SELECT runs.video_id, runs.run_id, runs.view_count, runs.likes, runs.dislikes ' \
                  'FROM runs INNER JOIN ' \
                  '((SELECT DISTINCT id AS video_id FROM videos ORDER BY polarity_composite DESC LIMIT 3) ' \
                  'UNION ' \
                  '(SELECT DISTINCT id AS video_id FROM videos ORDER BY polarity_composite ASC LIMIT 3)) AS top_bottom ' \
                  'ON runs.video_id = top_bottom.video_id ' \
                  'ORDER BY runs.video_id, runs.run_id'
            results = pd.read_sql_query(sql, conn)


            sql2 = """
                SELECT * 
                FROM `videos`
            """
            # pernw ta videos me tin megaliteri diafora sta views gia autes tis dio meres
            # kai provalw tin tasi ton likes kai ton dislike ws pros ta views tous
            all_videos_df = pd.read_sql_query(sql2, conn)
            all_videos_df.sort_values(["video_index_vpd"], ascending=False ,inplace=True)
            top_vpd = list(all_videos_df.head(3)['id'])

            # get all runs with id in top_vpd
            sql3 = """
                        SELECT * 
                        FROM `runs`
                    """
            total_runs = pd.read_sql_query(sql3, conn)

            # top video likes
            for i,id in enumerate(top_vpd):
                trend = total_runs[total_runs['video_id'] == id][['likes','view_count']]
                colors = ["#CD4FDE"]
                sns.set_palette(sns.color_palette(colors))
                sns.lmplot(x='likes', y='view_count', data=trend)
                plt.title('ViewCount vs.Likes for video {}, Top {} VPD'.format(id, i+1))
                plt.show()

            for i,id in enumerate(top_vpd):
                trend = total_runs[total_runs['video_id'] == id][['dislikes','view_count']]
                colors = ["#CD4FDE"]
                sns.set_palette(sns.color_palette(colors))
                sns.lmplot(x='dislikes', y='view_count', data=trend)
                plt.title('ViewCount vs.Likes for video {}, Top {} VPD'.format(id, i+1))
                plt.show()

            sns.reset_defaults()

            # get runs results for videos with top vpd
            top_vpd_runs = total_runs[total_runs['video_id'].isin(top_vpd)]
            top_vpd_pivot = pd.pivot_table(top_vpd_runs, index="run_id", columns="video_id", values="view_count")
            ax = top_vpd_pivot.plot(kind="line", rot=90, title="Views per run")
            ax.set_xlabel("Runs")
            ax.set_ylabel("View count in million")
            plt.show()


            print(all_videos_df)

            # Το dataframe ci_videos περιέχει τα id και τα ci των video
            # με τους 3 καλύτερους δείκτες ci
            # και τους 3 χειρότερους δείκτες ci
            ci_videos = pd.DataFrame(results)
            ci_videos = pd.pivot_table(ci_videos, index="run_id", columns="video_id", values="view_count")
            print(ci_videos)
            ax = ci_videos.plot(kind="line", rot=90, title="Views per run")
            ax.set_xlabel("Runs")
            ax.set_ylabel("View count in million")
            plt.show()

            ci_videos = pd.DataFrame(results)
            ci_videos = pd.pivot_table(ci_videos, index="run_id", columns="video_id", values="likes")
            print(ci_videos)
            ax = ci_videos.plot(kind="line", rot=90, title="Likes per run")
            ax.set_xlabel("Runs")
            ax.set_ylabel("Likes count")
            plt.show()

            ci_videos = pd.DataFrame(results)
            ci_videos = pd.pivot_table(ci_videos, index="run_id", columns="video_id", values="dislikes")
            print(ci_videos)
            ax = ci_videos.plot(kind="line", rot=90, title="Dislikes per run")
            ax.set_xlabel("Runs")
            ax.set_ylabel("Dislikes count")
            plt.show()

            conn.close()
        except :
            pass

        # Shows a heatmap of correlations among all columns of the dataset.
        # Negative correlations indicate that when the first column increases
        # the second column decreases and vice versa
        sqlEngine = create_engine('mysql+pymysql://root:@127.0.0.1/youtubeproject', pool_recycle=3600)
        conn = sqlEngine.connect()
        try :
            # Εκτελεί μία SQL SELECT στον πίνακα videos, για να φορτώσει σε dataframe
            # τους δείκτες που έχει καταγράψει το πρόγραμμα
            sql = pd.read_sql_query(
                '(SELECT DISTINCT id AS video_id, Duration, video_index_p, video_index_r, video_index_lpv, video_index_dpv, video_index_vpd, polarity_composite ' \
                'FROM videos ORDER BY polarity_composite DESC LIMIT 3) ' \
                'UNION ' \
                '(SELECT DISTINCT id AS video_id,  Duration, video_index_p, video_index_r, video_index_lpv, video_index_dpv, video_index_vpd, polarity_composite ' \
                'FROM videos ORDER BY polarity_composite ASC LIMIT 3)', conn)
            video_data = pd.DataFrame(sql, columns=['run_id', 'video_id', 'Duration', 'video_index_p', 'video_index_r',
                                                    'video_index_lpv', 'video_index_dpv', 'video_index_vpd',
                                                    'polarity_composite'])
        except :
            print('Error encountered. Resuming...')
        std_scale = preprocessing.StandardScaler().fit(video_data[['video_index_p', 'video_index_r', 'video_index_lpv',
                                                                   'video_index_dpv', 'video_index_vpd',
                                                                   'polarity_composite']])
        corr_video_data = std_scale.transform(video_data[['video_index_p', 'video_index_r', 'video_index_lpv',
                                                          'video_index_dpv', 'video_index_vpd', 'polarity_composite']])

        corr_video_data = video_data.corr().dropna(axis=0, how='all')
        corr_video_data = corr_video_data.dropna(axis=1, how='all')
        print(corr_video_data)

        fig, ax = plt.subplots(figsize=(12, 8))
        ax = sns.heatmap(corr_video_data, square=True, vmin=-1, vmax=1, center=0,
                         cmap=sns.diverging_palette(20, 220, n=200))
        plt.show()

    elif choice == '4' :
        # get videos trend for 24 hours
        print('i choose 4')
        get_trends_job()
