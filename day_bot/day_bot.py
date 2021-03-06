__author__ = 'gipmon'
import math
import time
import datetime
from random import randint
import json

from instagram.client import InstagramAPI


class DayBot:
    def __init__(self, config_file, tags_file):
        # Loading the configuration file, it has the access_token, user_id and others configs
        self.config = json.load(config_file)

        # Loading the tags file, it will be keep up to date while the script is running
        self.tags = json.load(tags_file)

        # file name to save the logs
        self.filename = self.config["path"] + self.config["prefix_name"] + time.strftime("%d%m%Y") + ".html"
        # Log file to output to html the debugging info about the script
        self.log_file = open(self.filename, "wb")

        # Initializing the Instagram API with our access token
        self.api = InstagramAPI(access_token=self.config["access_token"], client_secret=self.config['client_secret'])

        # Likes per tag rate
        self.likes_per_tag = math.trunc(min(self.config["follows_per_hour"],
                                            self.config["likes_per_hour"]) / len(self.tags["tags"]))

    def log_write(self, to_write):
        if self.filename != self.config["path"] + self.config["prefix_name"] + time.strftime("%d%m%Y") + ".html":
            self.log_file.close()
            self.filename = self.config["path"] + self.config["prefix_name"] + time.strftime("%d%m%Y") + ".html"
            self.log_file = open(self.filename, "wb")

        if isinstance(to_write, list):
            self.log_file.write(''.join(to_write) + "<br/>")
        else:
            self.log_file.write(str(to_write) + "<br/>")
            self.log_file.flush()

    def going_sleep(self, timer):
        sleep = randint(timer, 2 * timer)
        self.log_write("SLEEP " + str(sleep))
        time.sleep(sleep)

    def like_and_follow(self, media, likes_for_this_tag):
        try:
            var = self.api.user_relationship(user_id=media.user.id)

            if self.config["my_user_id"] != media.user.id:
                self.log_write("--------------")
                self.log_write(var)

                if var.outgoing_status == 'none':
                    self.log_write("LIKE RESULT:")
                    self.log_write(self.api.like_media(media_id=media.id))

                    self.log_write("FOLLOW RESULT:")
                    self.log_write(self.api.follow_user(user_id=media.user.id))

                    likes_for_this_tag -= 1

                    self.going_sleep(self.config["sleep_timer"])
                else:
                    self.going_sleep(self.config["sleep_timer"] / 2)

        except Exception, e:
            self.log_write(str(e))
            self.log_write("GOING SLEEP 30 min")
            time.sleep(1800)
            return self.like_and_follow(media, likes_for_this_tag)

        return likes_for_this_tag

    def run(self):
        # load the last verified date
        f = open('daybot_time', 'r')
        ts = float(f.readline())
        f.close()
        last_date = datetime.datetime.fromtimestamp(ts)

        # save the date in a file
        f = open('daybot_time', 'w')
        f.write(str(time.time()))
        f.close()

        while True:
            for tag in self.tags["tags"].keys():
                self.log_write("--------------------")
                self.log_write("TAG: " + tag)
                self.log_write("--------------------")

                self.log_write("--------------------")
                self.log_write("DICTIONARY STATUS:")

                for keys, values in self.tags["tags"].items():
                    self.log_write(keys)
                    if values is not None:
                        self.log_write(values)

                likes_for_this_tag = self.likes_per_tag

                while likes_for_this_tag > 0 and self.tags["tags"][tag] != 0:
                    if self.tags["tags"][tag] is None:
                        media_tag, self.tags["tags"][tag] = self.api.tag_recent_media(tag_name=tag,
                                                                                      count=likes_for_this_tag)
                    else:
                        media_tag, self.tags["tags"][tag] = self.api.tag_recent_media(tag_name=tag,
                                                                                      count=likes_for_this_tag,
                                                                                      max_tag_id=self.tags["tags"][tag])

                    self.log_write("API CALL DONE")

                    # if all the tags have date higher than the loaded it dies
                    date_all_higher = False

                    for media in media_tag:
                        date_all_higher |= (media.created_time > last_date)
                        # print media.created_time > last_date

                    if not date_all_higher:
                        self.log_write("DONE!")
                        exit(1)

                    if len(media_tag) == 0 or self.tags["tags"][tag] is None:
                        self.tags["tags"][tag] = 0
                        likes_for_this_tag = 0
                    else:
                        self.log_write(self.tags["tags"][tag])
                        self.tags["tags"][tag] = self.tags["tags"][tag].split("&")[-1:][0].split("=")[1]

                    for m in media_tag:
                        # verify if date is higher
                        likes_for_this_tag = self.like_and_follow(m, likes_for_this_tag)

                if reduce(lambda r, h: r and h[1] == 0, self.tags["tags"].items(), True):
                    self.log_write("END")
                    exit(1)


if __name__ == '__main__':
    bot = DayBot(open("config_bot.json", "r"), open("tags.json", "r"))
    bot.run()