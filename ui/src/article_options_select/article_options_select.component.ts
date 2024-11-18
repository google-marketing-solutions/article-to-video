import { Component, EventEmitter, Output } from '@angular/core';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleChange, MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSelectChange, MatSelectModule } from '@angular/material/select';


export class ArticleOptions {
  constructor(public kenBurns: boolean, public subtitles: boolean, public articleLanguage: string) {
  }
}

@Component({
  selector: 'article-options-select',
  standalone: true,
  imports: [MatInputModule, MatSlideToggleModule, MatSelectModule],
  templateUrl: './article_options_select.component.html',
  styleUrl: './article_options_select.component.css'
})
export class ArticleOptionsSelect {
  @Output() optionsChanged = new EventEmitter<ArticleOptions>();
  articleOptions = new ArticleOptions(true, true, "English (US)");

  changedSubtitles(event: MatSlideToggleChange) {
    this.articleOptions.subtitles = event.checked;
    this.optionsChanged.emit(this.articleOptions);
  }

  changedKenBurns(event: MatSlideToggleChange) {
    this.articleOptions.kenBurns = event.checked;
    this.optionsChanged.emit(this.articleOptions);
  }

  changedLanguage(event: MatSelectChange) {
    this.articleOptions.articleLanguage = event.value;
    this.optionsChanged.emit(this.articleOptions);
  }

}
