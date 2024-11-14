import { Component, Input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

@Component({
    selector: 'video-player',
    standalone: true,
    imports: [MatCardModule],
    templateUrl: './video_player.component.html',
    styleUrl: './video_player.component.css'
})
export class VideoPlayer {
    @Input() videoUri = "";
}
