# coding: utf-8

from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType
from pyspark.sql.types import StructField
from pyspark.sql.types import StructType
import pyspark.sql.functions as F


spark = SparkSession.builder.getOrCreate()

ratingSchema = StructType([
    StructField('user', IntegerType(), nullable=False),
    StructField('item', IntegerType(), nullable=False),
    StructField('rating', IntegerType(), nullable=False),
])


def loadRawData():
    url = 'jdbc:mysql://127.0.0.1:3306/albedo?user=root&password=123&verifyServerCertificate=false&useSSL=false'
    properties = {
        'driver': 'com.mysql.jdbc.Driver',
    }
    rawDF = spark.read.jdbc(url, table='app_repostarring', properties=properties)
    return rawDF


def recommendItems(rawDF, alsModel, username, topN=30):
    userID = rawDF \
        .where('from_username = "{0}"'.format(username)) \
        .select('from_user_id') \
        .take(1)[0]['from_user_id']

    userItemsDF = alsModel \
        .itemFactors. \
        selectExpr('{0} AS user'.format(userID), 'id AS item')
    userPredictedDF = alsModel \
        .transform(userItemsDF) \
        .select('item', 'prediction') \
        .orderBy('prediction', ascending=False) \
        .limit(topN)

    repoDF = rawDF \
        .groupBy('repo_id', 'repo_full_name', 'repo_language') \
        .agg(F.max('stargazers_count').alias('stargazers_count'))
    recommendedItemsDF = userPredictedDF \
        .join(repoDF, userPredictedDF['item'] == repoDF['repo_id'], 'inner') \
        .select('prediction', 'repo_full_name', 'repo_language', 'stargazers_count') \
        .orderBy('prediction', ascending=False)

    return recommendedItemsDF
