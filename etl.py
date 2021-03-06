import configparser
from datetime import datetime
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear


config = configparser.ConfigParser()
config.read('dl.cfg')

os.environ['AWS_ACCESS_KEY_ID'] = config['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = config['AWS_SECRET_ACCESS_KEY']


def create_spark_session():
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
        .getOrCreate()
    return spark


def process_song_data(spark, input_data, output_data):
    # get filepath to song data file
    song_data = os.path.join(input_data, 'data/song_data/*/*/*/*.json')

    # read song data file
    df = spark.read.json(song_data)

    # extract columns to create songs table
    songs_table = df['song_id', 'title', 'artist_id', 'year', 'duration']
    songs_table = songs_table.dropDuplicates(['song_id'])

    # write songs table to parquet files partitioned by year and artist
    songs_table.write \
        .partitionBy('year', 'artist_id') \
        .parquet(os.path.join(output_data, 'songs.parquet'))

    # extract columns to create artists table
    artists_table = df[
                    'artist_id',
                    'artist_name',
                    'artist_location',
                    'artist_latitude',
                    'artist_longitude']
    artists_table = artists_table.dropDuplicates(['artist_id'])

    # write artists table to parquet files
    artists_table.write.parquet(os.join.path(output_data, 'artists.parquet'))


def process_log_data(spark, input_data, output_data):
    # get filepath to log data file
    log_data = os.join.path(input_data, 'data/log_data/*.json')

    # read log data file
    df = spark.read.json(log_data)

    # filter by actions for song plays
    df = df.filter(df.page == 'NextSong')

    # extract columns for users table
    users_table = df[
                    'userId',
                    'firstName',
                    'lastName',
                    'gender',
                    'level']
    users_table = users_table.dropDuplicates(['userId'])

    # write users table to parquet files
    users_table.write.parquet(os.join.path(output_data, 'users.parquet'))

    # create timestamp column from original timestamp column
    get_timestamp = udf(lambda ts: int(int(ts)/1000))
    df = df.withColumn('timestamp', get_timestamp(df.ts))

    # create datetime column from original timestamp column
    get_datetime = udf(
                    lambda ts: datetime.utcfromtimestamp(ts)
                    .strftime('%Y-%m-%dT%H:%M:%SZ'))
    df = df.withColumn('datetime', get_datetime(df.ts))

    # extract columns to create time table
    time_table = df.select(
        col('datetime').alias('start_time'),
        hour('datetime').alias('hour'),
        dayofmonth('datetime').alias('day'),
        weekofyear('datetime').alias('week'),
        month('datetime').alias('month'),
        year('datetime').alias('year')
    )

    # write time table to parquet files partitioned by year and month
    time_table.write \
        .partitionBy('year', 'month') \
        .parquet(os.join.path(output_data, 'timetable.parquet'))

    # read in song data to use for songplays table
    song_data = os.path.join(input_data, 'data/song_data/*/*/*/*.json')
    song_df = spark.read.json(song_data)

    joined_df = df.join(song_df, song_df.title == df.song)

    # extract columns from joined song and log datasets to create
    # songplays table
    songplays_table = joined_df.select(
       col('datetime').alias('start_time'),
       year('datetime').alias('year'),
       month('datetime').alias('month'),
       col('userId').alias('user_id'),
       col('level'),
       col('song_id'),
       col('artist_id'),
       col('sessionId').alias('session_id'),
       col('location'),
       col('userAgent').alias('user_agent')
    )

    # write songplays table to parquet files partitioned by year and month
    songplays_table.write \
        .partitionBy('year', 'month') \
        .parquet(os.join.path(output_data, 'songplays.parquet'))


def main():
    spark = create_spark_session()
    input_data = "s3://awijaya-udacity-dend-project4/"
    output_data = "s3://awijaya-udacity-dend-project4/output/"
    process_song_data(spark, input_data, output_data)
    process_log_data(spark, input_data, output_data)


if __name__ == "__main__":
    main()
