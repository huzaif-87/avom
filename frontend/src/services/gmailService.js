/**
 * Gmail Candidate Communication Service
 *
 * Generates and opens a pre-populated Gmail compose window in a new tab.
 * Does NOT send emails automatically.
 * Does NOT require Gmail API credentials or OAuth tokens.
 * Utilizes standard Gmail URL parameters with safe URI encoding and security flags.
 */

/**
 * Builds a polite, professional recruitment email subject line.
 * @param {Object} candidate - Candidate details
 * @returns {string} Subject string
 */
export function buildRecruitmentSubject(candidate = {}) {
  const role = candidate.jobTitle ? candidate.jobTitle.trim() : 'the position';
  const name = candidate.name ? candidate.name.trim() : '';

  if (name) {
    return `Interview Invitation: Next Steps for ${role} - ${name}`;
  }
  return `Interview Invitation: Next Steps for ${role}`;
}

/**
 * Builds a polite recruitment email body inviting the candidate to connect.
 * @param {Object} candidate - Candidate details
 * @returns {string} Email body text
 */
export function buildRecruitmentBody(candidate = {}) {
  const name = candidate.name ? candidate.name.trim() : 'Candidate';
  const role = candidate.jobTitle ? candidate.jobTitle.trim() : 'the open position';
  const company = candidate.companyName ? candidate.companyName.trim() : 'our team';

  return `Dear ${name},

Thank you for your interest in the ${role} role at ${company}.

We reviewed your qualifications and background, and we are very impressed with your profile. We would like to invite you for an introductory conversation to discuss the position and learn more about your experience.

Please let us know your general availability over the coming days for a brief discussion.

Looking forward to connecting with you.

Best regards,
Talent Acquisition Team
TalentRank AI`;
}

/**
 * Opens Gmail compose in a new browser tab with pre-filled recipient, subject, and body.
 *
 * @param {Object} candidate
 * @param {string} candidate.name - Candidate's full name
 * @param {string} candidate.email - Candidate's email address
 * @param {string} [candidate.jobTitle] - Target job role title
 * @param {string} [candidate.companyName] - Hiring company name
 * @returns {boolean} True if window was opened, false if email missing or blocked
 */
export function openGmailCompose(candidate) {
  if (!candidate || !candidate.email || typeof candidate.email !== 'string') {
    console.warn('[gmailService] Candidate email is missing or invalid.');
    return false;
  }

  const email = candidate.email.trim();
  if (!email) {
    console.warn('[gmailService] Candidate email is empty.');
    return false;
  }

  const subject = candidate.subject || buildRecruitmentSubject(candidate);
  const body = candidate.body || buildRecruitmentBody(candidate);

  // Construct secure Gmail web compose URL with safe URI encoding
  const params = new URLSearchParams({
    view: 'cm',
    fs: '1',
    to: email,
    su: subject,
    body: body,
  });

  const gmailUrl = `https://mail.google.com/mail/?${params.toString()}`;

  // Open in new tab with security protections against reverse tabnabbing
  const newWindow = window.open(gmailUrl, '_blank', 'noopener,noreferrer');
  if (newWindow) {
    newWindow.opener = null;
    return true;
  }

  return false;
}
