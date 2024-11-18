import { Component, EventEmitter, inject, Output } from '@angular/core';
import { MatStepperModule } from '@angular/material/stepper';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { ArticleTextInput } from '../article_text_input/article_text_input.component';
import { ArticleImagesUpload } from '../article_images_upload/article_images_upload.component';
import { ArticleOptions, ArticleOptionsSelect } from '../article_options_select/article_options_select.component';
import { MatButtonModule } from '@angular/material/button';
import { AtvService, GeneratedVideo, GenerateVideoResponse } from '../atv.service';

@Component({
    selector: 'video-generation',
    standalone: true,
    imports: [MatStepperModule, ArticleTextInput, ArticleImagesUpload, MatButtonModule, ArticleOptionsSelect, MatCardModule, MatProgressSpinnerModule],
    templateUrl: './video_generation.component.html',
    styleUrl: './video_generation.component.css'
})
export class VideoGeneration {
    private atvService = inject(AtvService);
    @Output() videoGenerated = new EventEmitter<string>();
    videoId = "";

    articleText = '';
    articleOptions = new ArticleOptions(true, true, "English (US)");

    textChanged(articleText: string) {
        this.articleText = articleText;
    }

    articleOptionsChanged(articleOptions: ArticleOptions) {
        this.articleOptions = articleOptions;
    }

    generateVideo() {
        this.atvService.generateVideo(this.videoId, this.articleText, this.articleOptions).subscribe(response => this.videoGenerated.emit(response.path));
    }

    ngOnInit(): void {
        this.atvService.getId().subscribe(response => this.videoId = response.videoId);
    }
}
