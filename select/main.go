package main

import (
  "os"
  "log"
)

json_path := "video_list.json"

type videoInfo struct {
  title string
  url string
  top_comment string
}

func read_json() ([]videoInfo) {
}

func main() {
  if _, err := os.Stat(json_path); os.IsNotExist(err) {
    log.Fatal("no file named video_list.json")
  }
  video_info_list := read_json()
}
