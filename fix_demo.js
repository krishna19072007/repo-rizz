const fs = require('fs');

function fixFile(file) {
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/TRY REPO RIZZ[^\n]*/g, 'TRY REPO RIZZ →');
  fs.writeFileSync(file, content);
}

fixFile('src/app/analyze/page.tsx');
fixFile('src/components/hero/RepoInput.tsx');
