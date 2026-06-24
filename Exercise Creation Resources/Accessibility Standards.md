# Accessibility Standards

Accessibility is at the heart of our commitment to inclusivity. Our goal is to create learning content that empowers all students to succeed, regardless of their abilities, environment, or use of assistive technology. Aligned with global best practices, including the Web Content Accessibility Guidelines (WCAG), these standards demonstrate our commitment to integrating accessibility into our learning design.  
We follow the [four principles of accessibility](https://www.w3.org/WAI/WCAG22/Understanding/intro#understanding-the-four-principles-of-accessibility) outlined in the World Wide Web Consortium (W3C) Web Accessibility Initiative (WAI), which states that:  
Anyone who wants to use the Web must have content that is:

- **Perceivable** - Information and user interface components must be presentable to users in ways they can perceive.
- **Operable** - User interface components and navigation must be operable.
- **Understandable** - Information and the operation of user interface must be understandable
- **Robust** - Content must be robust enough that it can be interpreted reliably by a wide variety of user agents, including assistive technologies.

## Detailed Standards

Our primary goal is to meet **WCAG 2.1 AA** standards, but we are also able to meet many **WCAG 2.2 AAA** standards.

### Use Properly Nested Headings to Structure Text Content

Headings play a critical role in organizing content, making it easier for all users to navigate and understand. Proper use of headings benefits both sight-impaired users who rely on screen readers and typical students who visually skim content. On every page, headings should:

- **Start with the H2 level**: The top-level heading, H1, is the page title, which is automatically added to the page when it is rendered in the learner classroom.
- **Use headings in order, and do not skip levels.** Skipping levels breaks the page's hierarchy, which is very disruptive for learners using screen readers.
- **Keep Headings Clear and Descriptive**: Use concise, descriptive text in headings to summarize the content of each section.
- **Use headings to improve skimmability**: Thoughtfully written headings make content easier to scan, allowing users to quickly locate relevant information.
- **Avoid Misusing Bold Text**: Bold text may highlight content, but does not convey structural information to assistive technologies. Always use actual heading tags to mark headings.

**NEVER USE HEADINGS FOR FORMATTING\!\!\!\!**  
Although it can be tempting to make the page visually appealing, headings should be used only to establish hierarchy and page structure.

### Never Use Images of Text in the Classroom

While it may be tempting to use images of text for data tables or mathematical formulas, this can be particularly challenging for visually impaired learners, even when accompanied by well-written alt text. Images of text are inaccessible to screen readers and may become blurry when enlarged for learners with low vision.  
Instead, present any text or numerical information in the classroom as text in a text atom:

- Use Markdown tables for tabular data
- Use KaTeX formatting for mathematical equations

### Write Meaningful Alt Text

Alt text provides a textual alternative to images, ensuring that content is accessible to users who rely on screen readers or encounter issues loading images. Alt text should:

- **Be accurate and descriptive:** clearly and concisely describe the image's purpose and content, and focus on the essential information conveyed by the image.
- **Focus on what is relevant to the content:** Prioritize the most important information first and avoid vague or generic descriptions, such as "image of."
- **Avoid redundancy:** DO NOT repeat caption text or other information available in nearby text atoms unless necessary for clarity.
- **Follow best practices for screen reader users:** Use proper punctuation and capitalization and avoid using abbreviations or acronyms unless they are widely understood.

An AI-generated draft of alt text can be created in Studio (look for the ALT button in the image atom) or by uploading an image to the [Streamlit Alt Text Generator App](https://alt-text.streamlit.app/?template=Alt+Text+Generator). This draft must be reviewed by a human subject matter expert before the image content is released to learners.

#### Example:

For a diagram illustrating the steps in a software development lifecycle:

##### ✅ Do this

*Diagram showing the stages of software development: planning, analysis, design, development, testing, deployment, and maintenance.*

##### ❌ Don’t do this

*Image of a software development lifecycle.*

### Write Descriptive Hyperlinks

Hyperlinks should include the title and source or author of the resource to provide context, helping users understand what to expect before clicking. This is especially important for accessibility, as screen readers rely on clear, descriptive links to guide users effectively. Including this information ensures transparency, improves usability and builds trust by clearly attributing content to its source.  
Descriptive hyperlinks can also help our maintenance team identify the referenced information so they can more easily replace a link if the resource moves to a different URL or is removed from its original source.

#### ✅ Do this

**For links that reference documentation:** 

- Use the title of the resource, e.g., [Amazon EC2 Documentation](https://docs.aws.amazon.com/ec2/index.html?nc2=h_ql_doc_ec2)   
- If you are referencing a specific section or page, include title of the resource followed by the section name after a colon [Amazon EC2 Documentation: EC2 Instance Types](https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-types.html)  
- If the specific reference is nested in the resource, use arrows to indicate the navigation, e.g., [MDN Web Docs: JavaScript Reference > Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)

**For links to blog posts or online articles:**

- Use the name of the author and post title: [Amy Leak: Writing good text alternatives](https://medium.com/@amyalexandraleak/should-you-use-alt-text-or-a-caption-48311e259ded)
- Use blog name and post title: [Deeplearning.AI Blog: Essential Python Libraries for Machine Learning and Data Science](https://www.deeplearning.ai/blog/essential-python-libraries-for-machine-learning-and-data-science/)

**For links that share files:** 

- Tell users the link type when adding a link to a file by adding the file type in parentheses, e.g. [Accessibility Checklist (pdf)](https://video.udacity-data.com/topher/2024/November/673f4c4e_accessibility-checklist/accessibility-checklist.pdf) or [Propose Your Own AI Use Case Template (docx)](https://video.udacity-data.com/topher/2024/October/670bdbdc_propose-your-own-ai-use-case-project-template-v10.24/propose-your-own-ai-use-case-project-template-v10.24.docx)

#### ❌ Don’t do this

Use [here](https://giphy.com/gifs/snl-l396WcD0OCoCrYm6A) or [link](https://www.youtube.com/watch?v=DwRXI-y6M9o) as link text.

### Avoid Using Color to Distinguish Differences

Relying solely on color to convey information can create barriers for users with visual impairments, including color blindness. To ensure accessibility, always use additional cues—such as text labels, patterns, or icons—alongside color to communicate differences. This approach ensures that all users can understand the content, regardless of their ability to perceive color.

### Pay Attention to Color Contrast

Adequate color contrast between text and its background is crucial for readability, particularly for users with visual impairments. To meet **WCAG 2.1 AA** standards, text must achieve the following minimum contrast ratios:

- **4.5:1** for normal text.
- **3:1** for large text.

Ensuring proper contrast enhances visibility for all users, improving accessibility and overall usability.  
The [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) can be used to check the contrast between two colors using hex codes, but we recommend using the [WAVE Browser Extension](https://wave.webaim.org/extension/) to evaluate contrast directly in your browser window (Chrome, Firefox, or Microsoft Edge).

## Want to learn more about Accessibility?

### General Information and WCAG Standards

- [WCAG 2.2 Understanding Docs: Understanding the Four Principles of Accessibility](https://www.w3.org/WAI/WCAG22/Understanding/intro#understanding-the-four-principles-of-accessibility) gives a good overview of the four principles that are necessary to make the web accessible to all users.
- [How to Meet WCAG (Quick Reference)](https://www.w3.org/WAI/WCAG22/quickref/) shares details about how to meet each standard, including both sufficient techniques and failures.
  - [1.1.1 Non-text Content](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C121%2C246%2C314#non-text-content)
  - [1.2.2 Captions (Prerecorded)](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C121%2C246%2C314%2C122#captions-prerecorded)
  - [1.2.3 Audio Description or Media Alternative (Prerecorded)](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C121%2C122%2C246%2C314#audio-description-or-media-alternative-prerecorded)
  - [1.2.5 Audio Description (Prerecorded)](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C121%2C122%2C123%2C246%2C314#audio-description-prerecorded)
  - [1.3.2 Meaningful Sequence](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C121%2C122%2C123%2C125%2C128%2C131%2C246%2C314%2C132#meaningful-sequence)
  - [1.4.1 Use of Color](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview#use-of-color)
  - [1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview#contrast-minimum)
  - [1.4.5 Images of Text](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview#images-of-text)
  - [2.4.2 Page Titled](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview#page-titled)
  - [2.4.4 Link Purpose (In Context)](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview#link-purpose-in-context)
  - [2.4.6 Headings and Labels](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111#headings-and-labels)
  - [2.4.10 Section Headings](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111#section-headings)
  - [3.1.3 Unusual Words](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C246#unusual-words)
  - [3.1.4 Abbreviations](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C246#abbreviations)
  - [3.1.5 Reading Level](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&showtechniques=111%2C246#reading-level)

### Color and Contrast

- [Accessibility Bytes No. 2: Color Contrast](https://www.section508.gov/blog/accessibility-bytes/color-contrast/)
- [Accessibility Bytes No. 3: Use of Color](https://www.section508.gov/blog/accessibility-bytes/use-of-color/)
- [Understanding Success Criterion 1.4.1: Use of Color | WAI | W3C](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html)
- [3 Common Color Accessibility Issues One Can Easily Avoid | Deque](https://www.deque.com/blog/3-common-color-accessibility-issues-one-can-easily-avoid/)

### Alt Text

- [Write helpful alt text  |  Technical Writing  |  Google for Developers](https://developers.google.com/tech-writing/accessibility/self-study/write-alt-text?authuser=002)  
- [Amy Leak: Writing good text alternatives](https://medium.com/@amyalexandraleak/should-you-use-alt-text-or-a-caption-48311e259ded)  
- [Accessibility Bytes No. 5: Alternative Text](https://www.section508.gov/blog/accessibility-bytes/alternative-text/)  
- [How-to: Are you making these five mistakes when writing alt text? - The A11Y Project](https://www.a11yproject.com/posts/are-you-making-these-five-mistakes-when-writing-alt-text/)

### Headings

- [How-to: Accessible heading structure - The A11Y Project](https://www.a11yproject.com/posts/how-to-accessible-heading-structure/)
- [Accessibility Bytes No. 6: Document Headings](https://www.section508.gov/blog/accessibility-bytes/document-headings/)
- [Essential Guide to Heading Accessibility in Web Development](https://www.a11y-collective.com/blog/accessibility-headings/)

### Hyperlinks

- [Accessibility Bytes No. 4: Descriptive Links and Hypertext](https://www.section508.gov/blog/accessibility-bytes/descriptive-links-and-hypertext/)
- [WC3 | WAI: Understanding Success Criterion 2.4.4: Link Purpose (In Context) | WAI | W3C](https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html)

### Markdown Tables

- [Markdown Tables generator - TablesGenerator.com](https://www.tablesgenerator.com/markdown_tables)
- [Organizing information with tables - GitHub Docs](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables)

### KaTeX

- [Supported Functions · KaTeX](https://katex.org/docs/supported.html)