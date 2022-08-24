import ast
import findspark
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from datetime import timedelta as td
from pyspark.sql.window import Window

findspark.init()


PATH_TO_S3_JSON_FOLDER = "s3a://biking-data/*"
PATH_TO_S3_RESULTS_FOLDER = "s3a://biking-results/"


spark = (
    SparkSession.builder.appName("Aggregating Hamburg Bike Stations")
    .config("spark.pyspark.python", "python")
    .getOrCreate()
)


df = spark.read.format("json").load(PATH_TO_S3_JSON_FOLDER, multiLine=True)

exploded_df = df.select(
    df.thingID,
    df.description,
    df.coordinatesX,
    df.coordinatesY,
    F.explode(df.obs).alias("obs"),
)

obs_df = exploded_df.select(
    exploded_df.thingID,
    exploded_df.description,
    exploded_df.coordinatesX,
    exploded_df.coordinatesY,
    exploded_df.obs.observationID.alias("observationID"),
    exploded_df.obs.Result.alias("Result"),
    exploded_df.obs.resultTime.alias("resultTime"),
)

obs_df = obs_df.withColumn(
    "resultTime", F.to_timestamp("resultTime", "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
)
obs_df = obs_df.withColumn("resultHour", F.hour(obs_df.resultTime))
obs_df = obs_df.withColumn("resultWeekday", F.dayofweek(obs_df.resultTime))
obs_df = obs_df.withColumn("resultTimeTrunct", F.date_trunc("hour", obs_df.resultTime))


agg_df = obs_df.groupby(
    "thingID", "description", "coordinatesX", "coordinatesY", "resultTimeTrunct"
).agg(F.mean("Result"))
min_date_hour = agg_df.select(F.min("resultTimeTrunct")).collect()[0][0]
max_date_hour = agg_df.select(F.max("resultTimeTrunct")).collect()[0][0]


def get_delta(d1, d2):
    delta = d2 - d1
    return delta


delta = get_delta(min_date_hour, max_date_hour)
hour_list = []
for i in range(delta.days * 24 + 1):
    hour_list.append(min_date_hour + td(hours=i))
all_hours_df = spark.createDataFrame([{"resultTimeTrunct": x} for x in hour_list])


result_df = all_hours_df.crossJoin(agg_df.select("thingID").distinct()).join(
    agg_df, ["thingID", "resultTimeTrunct"], "left"
)

windowSpec = Window.partitionBy("thingID").orderBy("resultTimeTrunct")
result_df = result_df.withColumn(
    "Result", F.coalesce("avg(Result)", F.last("avg(Result)", True).over(windowSpec))
)
result_df = result_df.withColumn(
    "description",
    F.coalesce("description", F.last("description", True).over(windowSpec)),
)
result_df = result_df.withColumn(
    "coordinatesX",
    F.coalesce("coordinatesX", F.last("coordinatesX", True).over(windowSpec)),
)
result_df = result_df.withColumn(
    "coordinatesY",
    F.coalesce("coordinatesY", F.last("coordinatesY", True).over(windowSpec)),
)
result_df = result_df.drop("avg(Result)")


final_df = result_df.withColumn("resultHour", F.hour(result_df.resultTimeTrunct))
final_df = final_df.withColumn("resultWeekday", F.dayofweek(final_df.resultTimeTrunct))

final_agg_df = final_df.groupby(
    "thingID", "description", "coordinatesX", "coordinatesY", "resultHour"
).agg(F.mean("Result").alias("average_res"))


final_agg_df.coalesce(1).write.format("csv").option("header", "true").save(
    "results/all_stations_by_hour.csv", mode="overwrite"
)
