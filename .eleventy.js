// .eleventy.js
module.exports = function () {
  return {
    dir: {
      input: "content",       // <— tell Eleventy your input folder is /content
      includes: "_includes",  // <— so layouts live at /content/_includes
      output: "_site"
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk"
  };
};
