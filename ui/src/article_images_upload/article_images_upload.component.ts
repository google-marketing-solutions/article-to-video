import { Component, inject, Input } from '@angular/core';
import { AtvService, ImageUploadResponse } from '../atv.service';
import { MatButtonModule } from '@angular/material/button';
import { FormControl } from '@angular/forms';

@Component({
  selector: 'article-images-upload',
  standalone: true,
  imports: [MatButtonModule],
  templateUrl: './article_images_upload.component.html',
  styleUrl: './article_images_upload.component.css'
})
export class ArticleImagesUpload {
  private atvService = inject(AtvService);
  images: string[] = [];
  @Input() videoId = '';

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const files = (event.target as HTMLInputElement).files as FileList;
    if (files.length > 0) {
      let observables = this.atvService.uploadImages(this.videoId, files);
      observables.forEach(observable => {
        observable.subscribe(result => {
          this.images.push("/video/" + this.videoId + "/image/" + result.file);
        })
      })
    }
    input.value = "";
  }

}
