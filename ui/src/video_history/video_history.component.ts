import { Component, EventEmitter, inject, Output } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule, MatSelectionListChange } from '@angular/material/list';
import { AtvService, GeneratedVideo } from '../atv.service';

@Component({
    selector: 'video-history',
    standalone: true,
    imports: [MatCardModule, MatListModule, MatIconModule],
    templateUrl: './video_history.component.html',
    styleUrl: './video_history.component.css'
})
export class VideoHistory {
    private atvService = inject(AtvService);
    videos: GeneratedVideo[] = []
    @Output() videoSelected = new EventEmitter<string>();

    videoClicked(videoUri: string) {
        this.videoSelected.emit(videoUri);
    }

    ngOnInit(): void {
        this.atvService.getLastGeneratedVideos().subscribe(response => this.videos = response.videos);
    }
}
