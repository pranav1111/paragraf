"""One-off: writes the Claude-drafted gold set (reviewed=false). Pranav reviews it with scripts/review_gold.py."""
import json
from pathlib import Path

Q = []  # (type, lang, question, gold, reference, notes)
def q(t, lang, question, gold, reference, notes=""):
    Q.append((t, lang, question, gold, reference, notes))

# --- GDPR, direct (18) -------------------------------------------------------------------------
q("direct", "en", "What are the principles relating to the processing of personal data under the GDPR?", ["GDPR-art5"],
  "Lawfulness, fairness and transparency; purpose limitation (specified, explicit, legitimate purposes); data minimisation (adequate, relevant, limited to what is necessary); accuracy; storage limitation (no longer than necessary); integrity and confidentiality (appropriate security); and accountability (the controller is responsible for and must be able to demonstrate compliance).")
q("direct", "en", "On which legal bases may personal data be processed?", ["GDPR-art6"],
  "At least one of: consent; necessity for a contract with the data subject (or pre-contractual steps at their request); a legal obligation of the controller; vital interests; a task in the public interest or official authority; legitimate interests of the controller or a third party unless overridden by the data subject's interests or rights (not available to public authorities performing their tasks).")
q("direct", "en", "Can a data subject withdraw consent, and what conditions apply?", ["GDPR-art7"],
  "Yes, at any time. Withdrawal does not affect the lawfulness of processing before it. The data subject must be informed of this before giving consent, and withdrawing must be as easy as giving consent. The controller must be able to demonstrate that consent was given.")
q("direct", "en", "From what age can a child consent to information society services without parental approval?", ["GDPR-art8"],
  "From 16. Below 16, processing is lawful only if consent is given or authorised by the holder of parental responsibility. Member States may set a lower age, but not below 13.")
q("direct", "en", "Which types of personal data are special categories under the GDPR?", ["GDPR-art9"],
  "Data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs or trade union membership; genetic data; biometric data for uniquely identifying a person; health data; data concerning sex life or sexual orientation. Processing is prohibited unless an exception in Art. 9(2) applies, e.g. explicit consent.")
q("direct", "en", "How quickly must a controller respond to a request from a data subject exercising their rights?", ["GDPR-art12"],
  "Without undue delay and in any event within one month of receiving the request. This can be extended by two further months where necessary (complexity, number of requests); the data subject must be told about the extension and the reasons within the first month.")
q("direct", "en", "What information does the right of access give a data subject?", ["GDPR-art15"],
  "Confirmation whether their data are processed, access to the data and a copy, plus: purposes, categories of data, recipients, storage period (or criteria), the rights to rectification, erasure, restriction and objection, the right to complain to a supervisory authority, the source of the data, and the existence of automated decision-making including profiling with meaningful information about the logic involved.")
q("direct", "en", "Under which conditions must personal data be erased?", ["GDPR-art17"],
  "Without undue delay when: the data are no longer necessary; consent is withdrawn and there is no other legal ground; the data subject objects under Art. 21 and there are no overriding legitimate grounds (or objects to direct marketing); the data were processed unlawfully; erasure is required by a legal obligation; or the data were collected in relation to information society services offered to a child (Art. 8(1)).")
q("direct", "en", "What does the right to data portability include?", ["GDPR-art20"],
  "Receiving the personal data one has provided in a structured, commonly used and machine-readable format and transmitting them to another controller without hindrance, where processing is based on consent or a contract and carried out by automated means; direct transmission between controllers where technically feasible. It does not apply to processing for tasks in the public interest or official authority.")
q("direct", "en", "Can I object to my personal data being used for direct marketing?", ["GDPR-art21"],
  "Yes, at any time, including profiling related to direct marketing. After the objection the data must no longer be processed for such purposes. The right must be explicitly brought to the data subject's attention at the latest at the first communication.")
q("direct", "en", "What protection does the GDPR give against decisions based solely on automated processing?", ["GDPR-art22"],
  "A right not to be subject to a decision based solely on automated processing, including profiling, that produces legal or similarly significant effects. Exceptions: necessary for a contract, authorised by law with safeguards, or explicit consent. In the contract and consent cases the controller must at least provide the right to human intervention, to express one's point of view and to contest the decision.")
q("direct", "en", "What does data protection by design and by default require?", ["GDPR-art25"],
  "The controller must implement appropriate technical and organisational measures (e.g. pseudonymisation) that put data-protection principles such as data minimisation into effect, both when deciding the means of processing and during processing. By default, only data necessary for each specific purpose may be processed (amount collected, extent of processing, storage period, accessibility), and data must not be made accessible to an indefinite number of people without the individual's intervention.")
q("direct", "en", "What must a contract between a controller and a processor contain?", ["GDPR-art28"],
  "A binding contract setting out subject-matter, duration, nature and purpose of processing, type of personal data, categories of data subjects and the controller's obligations and rights. The processor must: process only on documented instructions; ensure confidentiality of authorised persons; take the security measures of Art. 32; use sub-processors only with authorisation; assist the controller (data subject rights, Art. 32–36 obligations); delete or return data at the end; and provide information and allow audits.")
q("direct", "en", "Which organisations are exempt from keeping records of processing activities?", ["GDPR-art30"],
  "Enterprises or organisations employing fewer than 250 persons, unless the processing is likely to result in a risk to rights and freedoms, is not occasional, or includes special categories of data (Art. 9(1)) or data on criminal convictions and offences (Art. 10).")
q("direct", "en", "Which security measures does the GDPR mention for the security of processing?", ["GDPR-art32"],
  "Technical and organisational measures appropriate to the risk, including as appropriate: pseudonymisation and encryption; ensuring ongoing confidentiality, integrity, availability and resilience of systems and services; the ability to restore availability and access to data in a timely manner after an incident; and a process for regularly testing, assessing and evaluating the effectiveness of the measures.")
q("direct", "en", "When must individuals be informed about a personal data breach?", ["GDPR-art34"],
  "When the breach is likely to result in a high risk to their rights and freedoms: without undue delay, in clear and plain language. Not required if the data were protected (e.g. encrypted), if later measures mean the high risk is no longer likely, or if it would involve disproportionate effort (then a public communication instead).")
q("direct", "en", "When is a data protection impact assessment required?", ["GDPR-art35"],
  "Before processing that is likely to result in a high risk to rights and freedoms (in particular with new technologies), and in particular for: (a) systematic and extensive evaluation of personal aspects based on automated processing including profiling with legal or similarly significant effects; (b) large-scale processing of special categories or criminal conviction data; (c) systematic monitoring of a publicly accessible area on a large scale.")
q("direct", "en", "What is the maximum administrative fine under the GDPR?", ["GDPR-art83"],
  "Up to EUR 20 000 000 or, for an undertaking, up to 4 % of total worldwide annual turnover of the preceding financial year, whichever is higher (e.g. for infringing the basic principles or data subjects' rights). A lower tier of up to EUR 10 000 000 or 2 % applies to other obligations (e.g. Articles 8, 25–39).")

# --- AI Act, direct (14) -----------------------------------------------------------------------
q("direct", "en", "How does the AI Act define an AI system?", ["AIACT-art3"],
  "A machine-based system designed to operate with varying levels of autonomy, that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, infers from the input it receives how to generate outputs such as predictions, content, recommendations or decisions that can influence physical or virtual environments.")
q("direct", "en", "What does the AI Act require regarding AI literacy?", ["AIACT-art4"],
  "Providers and deployers must take measures to ensure, to their best extent, a sufficient level of AI literacy of their staff and other persons operating or using AI systems on their behalf, taking into account their technical knowledge, experience, education and training, the context of use and the persons on whom the systems are used.")
q("direct", "en", "Which AI practices are prohibited under the AI Act?", ["AIACT-art5"],
  "Among others: subliminal, manipulative or deceptive techniques causing significant harm; exploiting vulnerabilities due to age, disability or social/economic situation; social scoring leading to detrimental treatment; predicting the risk of committing criminal offences based solely on profiling or personality traits; untargeted scraping of facial images to build facial recognition databases; emotion recognition in the workplace and education (except medical or safety reasons); biometric categorisation to infer sensitive characteristics; real-time remote biometric identification in public spaces for law enforcement except in narrowly defined cases.",
  "Citation-coverage case: the model listed 8 items with all citations only at the end (Phase 7).")
q("direct", "en", "When is an AI system classified as high-risk?", ["AIACT-art6"],
  "(1) When it is a safety component of a product, or itself a product, covered by the Union harmonisation legislation in Annex I and required to undergo a third-party conformity assessment; or (2) when it is listed in Annex III. An Annex III system is not high-risk if it does not pose a significant risk of harm (e.g. it only performs a narrow procedural task), but it is always high-risk if it performs profiling of natural persons.")
q("direct", "en", "What data requirements apply to training data of high-risk AI systems?", ["AIACT-art10"],
  "Training, validation and testing data sets must meet quality criteria and be subject to appropriate data governance and management practices (design choices, data collection and origin, preparation, assumptions, availability and suitability, examination of possible biases, identification of gaps). They must be relevant, sufficiently representative and, to the best extent possible, free of errors and complete.")
q("direct", "en", "What does the AI Act require regarding logging for high-risk AI systems?", ["AIACT-art12"],
  "High-risk AI systems must technically allow the automatic recording of events (logs) over the lifetime of the system, to ensure traceability appropriate to the intended purpose, e.g. to identify situations that may present a risk or a substantial modification, to support post-market monitoring and to monitor operation.")
q("direct", "en", "What does human oversight of high-risk AI systems mean under the AI Act?", ["AIACT-art14"],
  "High-risk AI systems must be designed so that natural persons can effectively oversee them while in use (including through human-machine interface tools), to prevent or minimise risks to health, safety and fundamental rights. Measures are commensurate with risk, autonomy and context, built in by the provider or implemented by the deployer; overseers must be able to understand the system's capacities and limitations, be aware of automation bias, interpret the output, decide not to use or override it, and interrupt or stop the system.")
q("direct", "en", "What are the obligations of deployers of high-risk AI systems?", ["AIACT-art26"],
  "Use the system according to the instructions for use; assign human oversight to persons with the necessary competence, training and authority; ensure input data under their control are relevant and representative; monitor operation, inform the provider and authorities of risks and suspend use where needed; report serious incidents; keep automatically generated logs for at least six months; inform workers' representatives and affected workers before workplace use; inform persons subject to decisions.")
q("direct", "en", "Who must carry out a fundamental rights impact assessment under the AI Act?", ["AIACT-art27"],
  "Before deploying a high-risk AI system under Art. 6(2) (except critical infrastructure, Annex III point 2): deployers that are bodies governed by public law or private entities providing public services, and deployers of systems for creditworthiness/credit scoring and for risk assessment and pricing in life and health insurance (Annex III points 5(b) and (c)).")
q("direct", "en", "What transparency obligations does the AI Act impose on AI systems that interact with people or generate content?", ["AIACT-art50"],
  "Providers must ensure people are informed that they are interacting with an AI system (unless obvious); providers of systems generating synthetic audio, image, video or text must mark outputs in a machine-readable format as artificially generated; deployers of emotion recognition or biometric categorisation must inform exposed persons; deployers of deep fakes must disclose that the content is artificially generated or manipulated (limited disclosure for evidently artistic or satirical works); AI-generated text published to inform the public on matters of public interest must be disclosed unless it underwent human review with editorial responsibility.")
q("direct", "en", "When is a general-purpose AI model presumed to have systemic risk?", ["AIACT-art51"],
  "When it has high impact capabilities; this is presumed when the cumulative amount of computation used for training exceeds 10^25 floating point operations. The Commission can amend the thresholds by delegated acts.")
q("direct", "en", "What are the obligations of providers of general-purpose AI models?", ["AIACT-art53"],
  "Draw up and keep up to date technical documentation (training, testing, evaluation results) for the AI Office and authorities; provide information and documentation to providers integrating the model; put in place a policy to comply with Union copyright law (including reservations of rights); publish a sufficiently detailed summary of the content used for training.")
q("direct", "en", "What fines can the AI Act impose for prohibited practices?", ["AIACT-art99"],
  "Non-compliance with the Art. 5 prohibitions: up to EUR 35 000 000 or, for an undertaking, up to 7 % of total worldwide annual turnover, whichever is higher. (Other operator obligations: EUR 15 000 000 / 3 %; incorrect information: EUR 7 500 000 / 1 %; for SMEs the lower of the two applies.) The lower amounts in Art. 100 apply only to Union institutions, bodies and agencies.",
  "Scope-error case: the model answered with Art. 100 (EUR 1.5m, Union institutions) although Art. 99 was retrieved (Phase 7).")
q("direct", "en", "From when does the AI Act apply?", ["AIACT-art113"],
  "It applies generally from 2 August 2026. Chapters I and II (general provisions incl. AI literacy, and the prohibitions) from 2 February 2025; Chapter III Section 4, Chapter V (general-purpose AI), Chapter VII, Chapter XII (penalties, except Art. 101) and Art. 78 from 2 August 2025; Art. 6(1) and its obligations from 2 August 2027.")

# --- NIS2, direct (10) -------------------------------------------------------------------------
q("direct", "en", "Which entities fall within the scope of NIS2?", ["NIS2-art2"],
  "Public or private entities of a type listed in Annex I or II that qualify as medium-sized enterprises or exceed the medium-sized ceilings and provide services or carry out activities in the Union. Regardless of size it also covers certain entities, e.g. providers of public electronic communications networks or services, trust service providers, TLD registries and DNS service providers, and sole providers of a service essential for critical societal or economic activities.")
q("direct", "en", "What is the difference between essential and important entities under NIS2?", ["NIS2-art3"],
  "Essential entities include Annex I entities exceeding the medium-sized ceilings, qualified trust service providers, TLD registries and DNS providers regardless of size, medium-sized providers of public electronic communications, certain public administration entities and entities identified by Member States. Entities of an Annex I or II type that do not qualify as essential are important entities.")
q("direct", "en", "What are the responsibilities of management bodies under NIS2?", ["NIS2-art20"],
  "They must approve the cybersecurity risk-management measures taken under Art. 21, oversee their implementation, and can be held liable for infringements. Members of management bodies must follow training, and entities are encouraged to offer similar training to employees regularly.")
q("direct", "en", "Which cybersecurity risk-management measures does NIS2 require?", ["NIS2-art21"],
  "Appropriate and proportionate technical, operational and organisational measures based on an all-hazards approach, including at least: risk analysis and information system security policies; incident handling; business continuity (backups, disaster recovery, crisis management); supply chain security; security in acquisition, development and maintenance including vulnerability handling and disclosure; assessing effectiveness; basic cyber hygiene and training; cryptography and encryption; HR security, access control and asset management; multi-factor authentication and secured communications.")
q("direct", "en", "What are the reporting deadlines for significant incidents under NIS2?", ["NIS2-art23"],
  "Early warning without undue delay and in any event within 24 hours of becoming aware; incident notification within 72 hours; an intermediate report on request; a final report not later than one month after the incident notification.")
q("direct", "en", "When is an incident considered significant under NIS2?", ["NIS2-art23"],
  "If it has caused or is capable of causing severe operational disruption of the services or financial loss for the entity, or has affected or is capable of affecting other natural or legal persons by causing considerable material or non-material damage.")
q("direct", "en", "What administrative fines does NIS2 provide for?", ["NIS2-art34"],
  "For infringements of Art. 21 or 23: essential entities a maximum of at least EUR 10 000 000 or at least 2 % of total worldwide annual turnover, whichever is higher; important entities a maximum of at least EUR 7 000 000 or at least 1.4 %. Fines must be effective, proportionate and dissuasive.")
q("direct", "en", "What is the role of a CSIRT in coordinated vulnerability disclosure under NIS2?", ["NIS2-art12"],
  "Each Member State designates one CSIRT as coordinator, acting as a trusted intermediary between persons reporting a vulnerability and the manufacturer or provider of the ICT product or service: identifying and contacting the entities concerned, assisting reporters, negotiating disclosure timelines and managing vulnerabilities affecting multiple entities. ENISA develops and maintains a European vulnerability database.")
q("direct", "en", "Can Member States require the use of certified ICT products under NIS2?", ["NIS2-art24"],
  "Yes. To demonstrate compliance with particular Art. 21 requirements, Member States may require essential and important entities to use ICT products, services and processes certified under European cybersecurity certification schemes adopted under Art. 49 of Regulation (EU) 2019/881, and they shall encourage the use of qualified trust services.")
q("direct", "en", "What supervisory powers do authorities have over essential entities under NIS2?", ["NIS2-art32"],
  "Supervisory measures must be effective, proportionate and dissuasive. Authorities can at least subject essential entities to on-site inspections and off-site supervision including random checks, regular and targeted security audits, ad hoc audits, security scans, and requests for information, access to data and documents and evidence of implemented cybersecurity policies.",
  "Reviewer: check the list in Art. 32(2) against the text; only point (a) was read when drafting.")

# --- Paraphrased: no shared keywords (10) --------------------------------------------------------
q("paraphrase", "en", "Our online shop was hacked and customer email addresses leaked. How long do we have to tell the data protection authority?", ["GDPR-art33"],
  "Without undue delay and, where feasible, not later than 72 hours after becoming aware of the breach, unless it is unlikely to result in a risk to people's rights and freedoms; if later, reasons for the delay must be given.")
q("paraphrase", "en", "Can a bank reject my loan application using only an algorithm, without any human looking at it?", ["GDPR-art22"],
  "Generally not, if the decision is based solely on automated processing and has legal or similarly significant effects, unless it is necessary for a contract, authorised by law, or based on explicit consent; even then the person has at least the right to human intervention, to express their view and to contest the decision.")
q("paraphrase", "en", "I want to switch to another streaming service. Can I take the data I gave the old service with me?", ["GDPR-art20"],
  "Yes, through the right to data portability: you can receive the data you provided in a structured, commonly used, machine-readable format and have it transmitted to another provider (directly where technically feasible), if processing is based on consent or contract and automated.")
q("paraphrase", "en", "My 14-year-old wants to sign up for a social media app. Does the app need permission from a parent?", ["GDPR-art8"],
  "Generally yes: where consent is the basis, a child under 16 needs consent given or authorised by the holder of parental responsibility, unless the Member State set a lower age (not below 13); the provider must make reasonable efforts to verify this.")
q("paraphrase", "en", "Is my employer allowed to use software that reads my emotions from my face during work?", ["AIACT-art5"],
  "No. Placing on the market, putting into service or using AI systems to infer emotions in the workplace or in education institutions is prohibited, except for medical or safety reasons.")
q("paraphrase", "en", "If I post an AI-generated fake video of a politician, do I have to say it is fake?", ["AIACT-art50"],
  "Yes. Deployers of AI systems that generate or manipulate image, audio or video content constituting a deep fake must disclose that the content has been artificially generated or manipulated (for evidently artistic, satirical or fictional works, disclosure is limited to not hampering the work).")
q("paraphrase", "en", "A ransomware attack shut down our energy company's systems. Who must we tell, and how fast?", ["NIS2-art23"],
  "If it is a significant incident, notify the CSIRT or competent authority: an early warning within 24 hours, an incident notification within 72 hours, a final report within one month after the notification; where appropriate also inform affected recipients of the services.")
q("paraphrase", "en", "Can the CEO be held personally accountable if the company ignores cybersecurity?", ["NIS2-art20"],
  "Under NIS2, management bodies must approve and oversee the cybersecurity risk-management measures and can be held liable for infringements of Art. 21; their members must also follow training.")
q("paraphrase", "en", "How long must a company keep the automatic records produced by a high-risk AI system it uses?", ["AIACT-art26"],
  "Deployers must keep the automatically generated logs under their control for a period appropriate to the intended purpose, of at least six months, unless Union or national law (in particular data protection law) provides otherwise.")
q("paraphrase", "en", "Our startup has 30 employees. Do we have to keep a register of all our data processing?", ["GDPR-art30"],
  "Organisations with fewer than 250 employees are exempt from keeping records of processing activities, but not if the processing is likely to result in a risk, is not occasional, or includes special categories or criminal conviction data.")

# --- Exact references (6) ------------------------------------------------------------------------
q("exact_ref", "en", "Art. 17 right to be forgotten", ["GDPR-art17"],
  "Art. 17 GDPR gives the right to erasure without undue delay, e.g. when data are no longer necessary, consent is withdrawn, the data subject objects, the data were processed unlawfully, a legal obligation requires it, or the data concern information society services offered to a child; with exceptions such as freedom of expression and legal obligations.")
q("exact_ref", "en", "What does Article 50 of the AI Act require?", ["AIACT-art50"],
  "Transparency: inform people that they are interacting with an AI system; mark synthetic content as artificially generated in a machine-readable way; inform people exposed to emotion recognition or biometric categorisation; disclose deep fakes and AI-generated text on matters of public interest.")
q("exact_ref", "en", "Summarise Art. 25 GDPR.", ["GDPR-art25"],
  "Data protection by design and by default: appropriate technical and organisational measures (e.g. pseudonymisation) that implement principles like data minimisation from the design stage, and by default only the data necessary for each purpose, not accessible to an indefinite number of people without the individual's intervention.")
q("exact_ref", "en", "What does Article 21 NIS2 regulate?", ["NIS2-art21"],
  "Cybersecurity risk-management measures: appropriate and proportionate technical, operational and organisational measures based on an all-hazards approach, with a minimum list including incident handling, business continuity, supply chain security, vulnerability handling, cyber hygiene and training, cryptography, access control and multi-factor authentication.")
q("exact_ref", "en", "Explain Art. 14 of the AI Act.", ["AIACT-art14"],
  "Human oversight: high-risk AI systems must be designed so that natural persons can effectively oversee them during use, to prevent or minimise risks; overseers must understand the system's limits, be aware of automation bias, interpret and be able to override the output, and stop the system.")
q("exact_ref", "en", "GDPR Article 28 processor obligations", ["GDPR-art28"],
  "Controllers may only use processors giving sufficient guarantees; sub-processors need prior written authorisation; a binding contract must specify the processing and oblige the processor to act only on documented instructions, ensure confidentiality, implement Art. 32 security, assist the controller, delete or return data at the end and allow audits.")

# --- Cross-law: two gold articles (6) -----------------------------------------------------------
q("cross_law", "en", "A hospital suffers a ransomware attack that also leaks patient data. Which reporting obligations apply under the GDPR and NIS2?", ["GDPR-art33", "NIS2-art23"],
  "GDPR: notify the supervisory authority without undue delay and where feasible within 72 hours (Art. 33), and the patients if the risk is high (Art. 34). NIS2 (hospitals are in scope as health-sector entities): early warning to the CSIRT or competent authority within 24 hours, incident notification within 72 hours, final report within one month after the notification.")
q("cross_law", "en", "Compare the maximum fines under the GDPR and NIS2.", ["GDPR-art83", "NIS2-art34"],
  "GDPR: up to EUR 20 000 000 or 4 % of worldwide annual turnover (lower tier EUR 10 000 000 / 2 %), whichever is higher. NIS2: essential entities a maximum of at least EUR 10 000 000 or 2 %, important entities at least EUR 7 000 000 or 1.4 %, whichever is higher.")
q("cross_law", "en", "What rights do people have when an algorithm or AI system makes a significant decision about them, under the GDPR and the AI Act?", ["GDPR-art22", "AIACT-art86"],
  "GDPR Art. 22: a right not to be subject to solely automated decisions with legal or similarly significant effects (with exceptions and safeguards such as human intervention and contesting the decision). AI Act Art. 86: a right to clear and meaningful explanations of the role of a high-risk AI system (Annex III) in a decision that produces legal or similarly significant adverse effects, and of the main elements of the decision.")
q("cross_law", "en", "What security measures do the GDPR and NIS2 require?", ["GDPR-art32", "NIS2-art21"],
  "GDPR Art. 32: technical and organisational measures appropriate to the risk, e.g. pseudonymisation, encryption, confidentiality/integrity/availability/resilience, timely restoration and regular testing. NIS2 Art. 21: all-hazards risk-management measures including incident handling, business continuity, supply chain security, vulnerability handling, cyber hygiene and training, cryptography, access control and multi-factor authentication.")
q("cross_law", "en", "Do both the GDPR and the AI Act require impact assessments before using risky systems?", ["GDPR-art35", "AIACT-art27"],
  "Yes. GDPR: a data protection impact assessment before processing likely to result in a high risk. AI Act: a fundamental rights impact assessment by certain deployers of high-risk AI systems (public bodies, private entities providing public services, credit scoring, life and health insurance pricing); it complements an existing DPIA.")
q("cross_law", "en", "Which training obligations exist for management under NIS2 and for staff using AI under the AI Act?", ["NIS2-art20", "AIACT-art4"],
  "NIS2: members of management bodies must follow training, and entities are encouraged to train employees regularly. AI Act: providers and deployers must ensure a sufficient level of AI literacy of staff dealing with AI systems.")

# --- German questions (8) ------------------------------------------------------------------------
q("direct", "de", "Wann muss eine Datenpanne gemeldet werden?", ["GDPR-art33"],
  "Unverzüglich und möglichst binnen 72 Stunden, nachdem die Verletzung bekannt wurde, an die zuständige Aufsichtsbehörde, es sei denn, sie führt voraussichtlich nicht zu einem Risiko für die Rechte und Freiheiten natürlicher Personen; bei späterer Meldung ist eine Begründung für die Verzögerung beizufügen.")
q("direct", "de", "Muss mein Unternehmen einen Datenschutzbeauftragten benennen?", ["GDPR-art37"],
  "Nach der DSGVO ja, wenn (a) die Verarbeitung von einer Behörde oder öffentlichen Stelle durchgeführt wird (außer Gerichten in justizieller Tätigkeit), (b) die Kerntätigkeit in Verarbeitungsvorgängen besteht, die eine umfangreiche regelmäßige und systematische Überwachung betroffener Personen erfordern, oder (c) die Kerntätigkeit in der umfangreichen Verarbeitung besonderer Kategorien (Art. 9) oder von Daten über strafrechtliche Verurteilungen (Art. 10) besteht.",
  "Incompleteness case found by Pranav: the model gave only case (b). § 38 BDSG (≥ 20 Personen) is not in the corpus.")
q("direct", "de", "Welche Bußgelder drohen bei Verstößen gegen die DSGVO?", ["GDPR-art83"],
  "Bis zu 20 000 000 EUR oder bei Unternehmen bis zu 4 % des weltweiten Jahresumsatzes des vorangegangenen Geschäftsjahres, je nachdem, welcher Betrag höher ist (z. B. bei Verstößen gegen die Grundsätze oder Betroffenenrechte); bis zu 10 000 000 EUR oder 2 % bei anderen Pflichten (z. B. Art. 8, 25–39).")
q("direct", "de", "Welche KI-Praktiken sind in der EU verboten?", ["AIACT-art5"],
  "U. a. manipulative oder täuschende Techniken mit erheblichem Schaden, das Ausnutzen von Schwächen (Alter, Behinderung, soziale oder wirtschaftliche Lage), Social Scoring, die Vorhersage von Straftaten allein auf Grundlage von Profiling, das ungezielte Auslesen von Gesichtsbildern, Emotionserkennung am Arbeitsplatz und in Bildungseinrichtungen (außer aus medizinischen oder Sicherheitsgründen), biometrische Kategorisierung nach sensiblen Merkmalen und biometrische Echtzeit-Fernidentifizierung im öffentlichen Raum zur Strafverfolgung (mit engen Ausnahmen).")
q("paraphrase", "de", "Müssen Mitarbeiter, die KI-Systeme nutzen, geschult werden?", ["AIACT-art4"],
  "Anbieter und Betreiber von KI-Systemen müssen Maßnahmen ergreifen, um nach besten Kräften sicherzustellen, dass ihr Personal und andere Personen, die in ihrem Auftrag mit KI-Systemen umgehen, über ausreichende KI-Kompetenz verfügen, unter Berücksichtigung von Kenntnissen, Erfahrung, Ausbildung und Einsatzkontext.")
q("direct", "de", "Welche Fristen gelten für die Meldung erheblicher Sicherheitsvorfälle nach NIS2?", ["NIS2-art23"],
  "Frühwarnung unverzüglich, spätestens innerhalb von 24 Stunden nach Kenntnisnahme; Meldung des Sicherheitsvorfalls innerhalb von 72 Stunden; auf Ersuchen ein Zwischenbericht; Abschlussbericht spätestens einen Monat nach der Meldung.")
q("paraphrase", "de", "Habe ich ein Recht zu erfahren, welche Daten ein Unternehmen über mich gespeichert hat?", ["GDPR-art15"],
  "Ja, das Auskunftsrecht: Bestätigung, ob Daten verarbeitet werden, Zugang und Kopie sowie Informationen zu Zwecken, Datenkategorien, Empfängern, Speicherdauer, Rechten auf Berichtigung, Löschung, Einschränkung und Widerspruch, Beschwerderecht, Herkunft der Daten und automatisierter Entscheidungsfindung einschließlich Profiling.")
q("direct", "de", "Wann gilt ein KI-System als Hochrisiko-KI-System?", ["AIACT-art6"],
  "(1) Wenn es Sicherheitsbauteil eines Produkts oder selbst ein Produkt nach den Harmonisierungsrechtsvorschriften in Anhang I ist und einer Konformitätsbewertung durch Dritte unterliegt, oder (2) wenn es in Anhang III aufgeführt ist; ein Anhang-III-System ist nicht hochriskant, wenn es kein erhebliches Risiko birgt (z. B. eng gefasste Verfahrensaufgabe), führt es aber Profiling natürlicher Personen durch, gilt es stets als hochriskant.")

# --- Unanswerable (8) --------------------------------------------------------------------------
UNANSWERABLE_EN = "Should abstain: not covered by the GDPR, the AI Act or NIS2."
UNANSWERABLE_DE = "Sollte ablehnen: nicht durch DSGVO, KI-Verordnung oder NIS2 geregelt."
q("unanswerable", "en", "What is the speed limit on the German Autobahn?", [], UNANSWERABLE_EN)
q("unanswerable", "de", "Wie hoch ist das Kindergeld in Deutschland?", [], UNANSWERABLE_DE)
q("unanswerable", "en", "What is the statutory minimum wage in Germany?", [], UNANSWERABLE_EN)
q("unanswerable", "en", "Who won the 2014 FIFA World Cup?", [], UNANSWERABLE_EN)
q("unanswerable", "en", "What is the maximum fine under the EU Cyber Resilience Act?", [], UNANSWERABLE_EN,
  "Near-domain trap: CRA is not in the corpus; a wrong answer would reuse NIS2 or AI Act fines.")
q("unanswerable", "en", "What does the Digital Services Act require from very large online platforms?", [], UNANSWERABLE_EN,
  "Near-domain trap: the DSA is not in the corpus.")
q("unanswerable", "de", "Was regelt das Bundesdatenschutzgesetz zum Beschäftigtendatenschutz?", [], UNANSWERABLE_DE,
  "Near-domain trap: the BDSG is not in the corpus.")
q("unanswerable", "de", "Wie viele Urlaubstage stehen Arbeitnehmern in Deutschland gesetzlich zu?", [], UNANSWERABLE_DE)

out = Path(__file__).with_name("gold.jsonl")
with out.open("w", encoding="utf-8") as f:
    for i, (t, lang, question, gold, ref, notes) in enumerate(Q, start=1):
        row = {"id": f"q{i:03d}", "lang": lang, "type": t, "question": question, "gold": gold,
               "reference": ref, "source": "claude-draft", "reviewed": False}
        if notes:
            row["notes"] = notes
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(f"wrote {len(Q)} questions to {out}")
