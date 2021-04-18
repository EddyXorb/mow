from video.transcodeallmovs import parser,call

if __name__ == "__main__":
    print("Transcode all movie files in folder. Specifiy folder..")
    args = parser.parse_args()
    call(args)