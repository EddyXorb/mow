import video.transcodeallmovs

if __name__ == "__main__":
    print("Transcode all movie files in folder. Specifiy folder..")
    args = video.transcodeallmovs.parser.parse_args()
    video.transcodeallmovs.call(args)