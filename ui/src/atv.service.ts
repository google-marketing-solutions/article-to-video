import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ArticleOptions } from './article_options_select/article_options_select.component';

export class VideoIdResponse {
  constructor(public video_id: string) { }
}

export class ImageUploadResponse {
  file = "";
}

export class GenerateVideoResponse {
  constructor(public status: string, public path: string) { }
}

export class GeneratedVideo {
  constructor(public uri: string, public date: string) { }
}

export class LastGeneratedVideosResponse {
  videos: GeneratedVideo[] = [];
}

@Injectable({
  providedIn: 'root',
})
export class AtvService {
  constructor(private http: HttpClient) {
  }

  getId(): Observable<VideoIdResponse> {
    // Use this to mock server response
    // return new Observable<VideoIdResponse>((subscriber) => subscriber.next(new VideoIdResponse("sadofjs-asdifj-asdfijas-asdijfasd")));
    return this.http.get<VideoIdResponse>('/video/new_id');
  }

  getLastGeneratedVideos(): Observable<LastGeneratedVideosResponse> {
    let lastGeneratedVideosResponse = new LastGeneratedVideosResponse();
    lastGeneratedVideosResponse.videos = [
      new GeneratedVideo("https://storage.googleapis.com/scramble-atv-gcs/5c64c1fe-d00f-478a-9faf-3fe6ae051bee.mp4", "Nov 14, 2024, 1:51:58 PM"),
      new GeneratedVideo("https://storage.googleapis.com/scramble-atv-gcs/0d4b754f-575a-43b3-be3f-d0b3cfff8d52.mp4", "Nov 14, 2024, 1:49:55 PM"),
      new GeneratedVideo("https://storage.googleapis.com/scramble-atv-gcs/224659d5-f6f6-45cd-9fce-255dd33a9862.mp4", "Nov 14, 2024, 9:46:41 AM"),
      new GeneratedVideo("https://storage.googleapis.com/scramble-atv-gcs/2c50259b-378b-42b1-9882-5a7e1124fecf.mp4", "Nov 6, 2024, 11:08:45 AM"),
      new GeneratedVideo("https://storage.googleapis.com/scramble-atv-gcs/d02d1688-9479-4bc9-9f43-32d33ff530ca.mp4", "Nov 6, 2024, 11:05:13 AM")
    ];
    return new Observable<LastGeneratedVideosResponse>((subscriber) => subscriber.next(lastGeneratedVideosResponse));
  }

  uploadImages(videoId: string, images: FileList): Observable<ImageUploadResponse>[] {
    let observables = [];
    for (let i = 0; i < images.length; i++) {
      let formData = new FormData();
      formData.append('file', images[i], images[i].name);
      observables.push(this.http.post<ImageUploadResponse>('/video/' + videoId + '/image/upload', formData));
    }
    return observables;
  }

  generateVideo(videoId: string, articleText: string, articleOptions: ArticleOptions): Observable<GenerateVideoResponse> {
    // Use this to mock server response.
    // return new Observable<GenerateVideoResponse>((subscriber) => subscriber.next(new GenerateVideoResponse("ok", "https://storage.googleapis.com/scramble-atv-gcs/d02d1688-9479-4bc9-9f43-32d33ff530ca.mp4")));
    return this.http.post<GenerateVideoResponse>('/video/' + videoId + '/generate', {
      article_content: articleText,
      burned_in_subtitles: articleOptions.subtitles,
      ken_burns: articleOptions.kenBurns,
      language_of_article: articleOptions.articleLanguage
    });
  }
}