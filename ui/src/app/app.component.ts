import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { VideoGeneration } from '../video_generation/video_generation.component';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { VideoPlayer } from '../video_player/video_player.component';
import { VideoHistory } from '../video_history/video_history.component';

import { AsyncPipe } from '@angular/common';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, VideoPlayer, VideoHistory, MatTabsModule, MatToolbarModule, VideoGeneration, MatCardModule, MatButtonModule, MatIconModule, AsyncPipe, MatProgressSpinnerModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  selectedTab = 0;
  watchingVideoUri = "";

  clearTab(index: number){
    if (index != 1) {
      this.watchingVideoUri = "";
    }
    this.selectedTab = index;
  }

  watch(videoUri: string) {
    this.selectedTab = 1;
    this.watchingVideoUri = videoUri;
  }
}
