# Packed transcripts

Phrase-level, grouped on silences ≥ 0.5s or speaker change.
Use `[start-end]` ranges to address cuts in the EDL.

## budget-free-website-startup-guide-clean  (duration: 12m 08.3s, 76 phrases)
  [000.00-004.84] SS0 This is a live website for my dad's hotel in Kerala, Ground Tourist Home.
  [005.48-023.20] SS0 It loads instantly on mobile. Guests can message directly on WhatsApp to book and hosting costs $0. The only thing I paid for was the custom web address which was under $10 for a year. No monthly agency fees, no subscriptions.
  [023.92-034.10] SS0 It took me 4 hours to build because I wasn't specific about the type of website I wanted due to which I ran into dealing with dependency conflicts and file limit error.
  [034.80-035.68] SS0 In this video,
  [036.18-045.36] SS0 I'll show you the exact step by step process using free AI tools and the simple fix so you can finish yours in under two hours.
  [046.16-049.92] SS0 This video is about creating a website for a small hotel business.
  [050.46-057.64] SS0 You can tweak based on your requirements so let's get started. When I sat down with my dad,
  [058.16-059.84] SS0 he didn't need anything fancy.
  [060.58-068.70] SS0 He needed guests to see the rooms and the rates and to reach the reception on WhatsApp or call the number on the website
  [069.22-071.24] SS0 that decided everything that followed.
  [071.88-077.14] SS0 Before you open any AI tool, get these together. This part is the most of the work.
  [077.66-086.10] SS0 You can create a prep doc in your local or in tools, check -in times,
  [086.70-093.88] SS0 it can include the Google map location of your business and also the phone number to reach out on WhatsApp as well as for the deception.
  [094.70-099.78] SS0 You can also store the real photos in your local, so when the website is getting created you can upload them.
  [100.52-104.16] SS0 And about two hours and the price of the domain, these are the things you need.
  [104.94-115.62] SS0 AI generates the code fast, but it can't guess your business. So if you are missing any details, leave it out and tell the AI to leave it out to else it will hallucinate.
  [116.68-120.22] SS0 The prep is the work. AI is the fast part.
  [120.98-122.76] SS0 So let's jump straight into the tool.
  [123.42-142.50] SS0 We are using Google AI Studio. Go to aistudio.google.com apps under settings in that you can choose the default version which is free Gemini 3.8. If you notice I have a pro subscription but that is not required to create a simple website.
  [143.06-145.38] SS0 Go to the prompt section under new app.
  [146.60-153.12] SS0 Here there is this mic where you can click and talk in simple human language about your requirements.
  [154.08-157.00] SS0 The golden rule of building with AI Studio is,
  [157.50-161.00] SS0 you provide the real world inputs like the Google map links,
  [161.54-162.30] SS0 real photos,
  [162.80-172.44] SS0 actual phone number and AI desktop research, design and coding. I'll put the detailed prompt in the pinned comment so you can copy paste it with your own details.
  [173.34-178.94] SS0 So this is the initial build and I'm just gonna keep it in default mode and hit send prompt.
  [179.58-184.34] SS0 So now you see the first prompt gave us a result in less than six minutes.
  [184.88-190.54] SS0 So this is a basic site which you receive once that initial prompt was given to AI Studio.
  [191.20-193.36] SS0 Now let's do an immediate reality chip.
  [193.98-196.80] SS0 Are the phone numbers and the rates exact?
  [197.56-200.30] SS0 Did AI insert fake generated room photos?
  [201.22-205.32] SS0 AI generated luxury suites that do not exist in real life.
  [206.32-218.48] SS0 If a guest shows up expecting an infinity pool because AI hallucinated it, you're going to have an upset customer. Let's make it real first photos. So click upload.
  [219.00-221.40] SS0 Add your real photos.
  [221.98-225.12] SS0 Tell the AI to swap out the placeholders.
  [225.92-226.76] SS0 Second,
  [227.62-228.64] SS0 distances.
  [229.34-238.82] SS0 Paste your Google map links and ask it to calculate travel times to key landmarks like the local waterfalls or the bus station.
  [239.50-247.76] SS0 Always verify these numbers yourself because AI will state a travel time with complete confidence even when it is completely wrong.
  [248.74-271.04] SS0 Third, the booking button. I'll show it to you in the actual website so if you click the booking button you can see it will prompt the user to select the type of the room they want if they need any extra mattress the check -in date check -out date number of huddles and it drafts a message automatically based on the selections you do.
  [271.62-278.10] SS0 Once you click it, it will send an enquiry via WhatsApp or you can click on reception and call and ask them directly.
  [279.18-283.18] SS0 We don't need a complicated booking engine, payment processors or a database.
  [283.78-285.20] SS0 The guest picks their dates,
  [285.70-289.10] SS0 taps the button and checks directly with the reception to confirm.
  [289.92-291.84] SS0 Here is the part where I got stuck.
  [292.76-293.44] SS0 Quick question.
  [294.42-300.42] SS0 If you ask an AI to build a website and give it no limits, what kind of site do you think it builds?
  [301.12-301.80] SS0 Hold that guess.
  [302.84-304.48] SS0 So, there are two kinds of websites,
  [305.00-306.34] SS0 a dynamic and a static.
  [306.96-312.36] SS0 A dynamic site knows who you are and changes for you, like Amazon shopping cart,
  [313.30-349.86] SS0 a train booking site or even your banking app, where you log in with your ID and it will show your balance because behind it there is a server and a database but a static site is like a brochure everyone sees the same page nothing is stored nobody locks in for a small hotel that is enough rooms rates and button to call a message so when I give AI studio no limits it built a dynamic site a full react app structured for logins databases and live bookings.
  [350.36-355.24] SS0 For a guest house it was built like a banking app and my dad needed a brochure.
  [355.92-363.64] SS0 When I tried to upload it in cloud player it hit the file size of 25 MIB and it failed.
  [364.66-368.84] SS0 It almost took me an hour to figure it out what is happening.
  [369.60-385.80] SS0 So I went back to Google AI studio and I just asked it to build a static website that is mobile friendly and can be hosted on cloudflare by drag and drop option. So after this prompt it recreated the website in simple static form.
  [386.76-393.06] SS0 Most of your guest will open this on a phone. So look at it on a phone before you publish.
  [393.64-406.24] SS0 So here you can select a phone option and you can see how it is. you can see that the menu and the WhatsApp is not completely visible and also just check whether anything spill off the site or a link is opening properly.
  [406.74-512.68] SS0 If something is off, what you can do is take a screenshot of that, put it over here in this area and just chat with AI to please fix that particular icon or that particular menu option and then it will be updated. it so after making those changes this is how my website actually looked like and after fixing it these icons are visible and you don't have to scroll to the right to see that it's all intact on a page because most of the guests will be reaching out the hotels via phone so it's very important to keep the phone interface smooth and easy okay another thing I want to tell you is if you go to the settings and if you want to restore a particular version of the change you made for the website you can select that from this area you can click this and if you want this particular click this and click restore version and that will restore that particular version of your website so it's not necessary that you have to go with the ultimate change you did you can switch back or undo the changes by doing that okay so once we are happy with how our website is looking you can go to this angle bracket which is next to preview click there click export there are different ways you can export to anti -gravity or you can push to GitHub or you can download as zip file I'll show you the easiest way now I have my code in the data with GitHub but you can this download data set. So click this option and that will download your file in your local as a zip.
  [513.72-525.40] SS0 Once you have it in your local click this and you can extract all and once it is extracted you can take this zip file which is for cloudflare.
  [526.98-545.22] SS0 You can open cloudflare drop and then you can drag this file and put it here so it's checking for the size and relevant checklist before uploading this and bringing it live
  [546.90-569.42] SS0 okay so once all the files are uploaded it is hosting the website when site is ready you can claim it click claim and it is going to click this and it is created this is hosted under my email ID and you can finish setting it up
  [570.08-588.78] SS0 okay so the site is live and you get a free cloudflare address open it on your phone tap every button and make sure all the buttons are working and before you buy a domain you can even share this URL if you're working for somebody to get a site created and update changes if needed.
  [589.28-615.48] SS0 In my case it was my dad I asked him to check every room every rate every number he knows the business right not me and after it is done you can buy a custom domain click purchase domain and groundtouristgroup.com just checking a domain like that and it's 11.17 CAD which is under $10 in USD for a year.
  [616.04-626.94] SS0 So you can buy that and the good part with Cloudflare is the renewal remains the same price and it will give you a HTTPS site so that is good.
  [629.12-647.20] SS0 Cloudflare sells domains at wholesale cost with zero markup. Mine was under $10 USD for the full year with no monthly hosting fees attached. Click Continue Payment and then click Confirm, link it to your project and your website is officially live to the world.
  [647.70-649.10] SS0 Next, let's do speed check.
  [649.70-669.64] SS0 There is a website called patespeed.web.dev which is a free Google tool that tests how fast your website loads and how well it performs especially on mobile devices. So go to page speedbrotweb.dev and paste your address and click analyze.
  [670.22-671.82] SS0 Make sure you select the mobile.
  [672.54-674.58] SS0 My first scores were not this, it was low.
  [675.12-684.68] SS0 So what I did is I went back to Google AI studio and with the screenshot and told it to fix it. Then I ran the test again and I got better scores.
  [685.78-691.70] SS0 I stopped there because I only wanted it to load fast on phone. There is something called agentic browsing.
  [692.24-707.12] SS0 Mine was 3 out of 4 so I didn't chase it like it was not needed for me. That's the entire process. My dad now has a clean fast website with zero ongoing hosting fee, built for under $10 total.
  [707.94-712.30] SS0 All the prompts, templates and steps are in the pinned comment below.
  [713.04-725.54] SS0 If this video helped, subscribe so you don't miss the next guy. Drop a comment below with the kind of businesses you are building a website for. And if you get stuck anywhere, let me know in the comments so I can help you out.
  [726.12-728.30] SS0 Thank you for watching. See you in the next video.
