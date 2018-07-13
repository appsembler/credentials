import React from 'react';
import PropTypes from 'prop-types';
import { Button } from '@edx/paragon';

import FoldingTable from './FoldingTable';
import ProgramIcon from './ProgramIcon';
import SendLearnerRecordModal from './SendLearnerRecordModal';
import ShareProgramRecordModal from './ShareProgramRecordModal';
import StringUtils from './Utils';
import trackEvent from './Analytics';

class ProgramRecord extends React.Component {
  constructor(props) {
    super(props);

    this.loadSendRecordModal = this.loadSendRecordModal.bind(this);
    this.loadShareModel = this.loadShareModel.bind(this);
    this.closeSendRecordModal = this.closeSendRecordModal.bind(this);
    this.closeShareModel = this.closeShareModel.bind(this);
    this.setActiveButton = this.setActiveButton.bind(this);
    this.downloadRecord = this.downloadRecord.bind(this);

    this.formatDate = this.formatDate.bind(this);
    this.formatGradeData = this.formatGradeData.bind(this);
    this.formatPercentage = this.formatPercentage.bind(this);
    this.state = {
      shareModelOpen: false,
      sendRecordModalOpen: false,
      isPublic: true,
      recordDownloaded: false,
    };
  }

  setActiveButton(button) {
    this.activeButton = button;
  }

  loadSendRecordModal(event) {
    this.setState({
      sendRecordModalOpen: true,
    });
    this.setActiveButton(event.target);
    trackEvent('edx.bi.credentials.program_record.send_started', {
      category: 'records',
      'program-uuid': this.props.uuid,
    });
  }

  loadShareModel(event) {
    this.setState({
      shareModelOpen: true,
    });
    this.setActiveButton(event.target);
    trackEvent('edx.bi.credentials.program_record.share_started', {
      category: 'records',
      'program-uuid': this.props.uuid,
    });
  }

  closeSendRecordModal() {
    this.setState({
      sendRecordModalOpen: false,
    });
    this.activeButton.focus();
  }

  closeShareModel() {
    this.setState({
      shareModelOpen: false,
    });
    this.activeButton.focus();
  }

  downloadRecord() {
    // TODO: Add functionality as part of LEARNER-5513
    this.setState({ recordDownloaded: true });
  }

  formatDate(isoDate) {
    if (!isoDate) {
      return isoDate;
    }

    const date = new Date(isoDate);

    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear().toString().slice(2)}`;
  }

  formatPercentage(decimal) {
    if (!decimal) {
      return decimal;
    }

    return `${parseInt(decimal * 100, 10)}%`;
  }

  formatGradeData() {
    const { grades } = this.props;

    return grades.map(course => ({
      ...course,
      // If certificate not earned hide some fields
      ...(!course.issue_date && { course_id: null }),
      ...(!course.issue_date && { letter_grade: null }),
      ...(!course.issue_date && { attempts: null }),
      percent_grade: this.formatPercentage(course.percent_grade),
      issue_date: this.formatDate(course.issue_date),
      status: course.issue_date ?
        <span className="badge badge-success">{gettext('Earned')}</span> :
        <span className="badge badge-default">{gettext('Not Earned')}</span>,
    }));
  }

  render() {
    const {
      learner,
      program,
      platform_name: platformName,
      isPublic,
      uuid,
      loadModalsAsChildren,
    } = this.props;
    const { sendRecordModalOpen, shareModelOpen } = this.state;
    const recordWrapperClass = 'program-record-wrapper';
    const defaultModalProps = {
      ...(loadModalsAsChildren && { parentSelector: `.${recordWrapperClass}` }),
    };

    return (
      <main className={recordWrapperClass}>
        {!isPublic &&
          <section className="program-record-actions program-record-row">
            <a href="/records/" className="top-bar-link flex-4">
              <span className="fa fa-caret-left" aria-hidden="true" /> {gettext('Back to My Records')}
            </a>
            <Button
              label={gettext('Send Learner Record')}
              className={['btn-primary']}
              onClick={this.loadSendRecordModal}
            />
            <Button
              label={gettext('Share')}
              className={['btn-secondary']}
              onClick={this.loadShareModel}
              inputRef={this.setShareButton}
            />
          </section>
        }
        {isPublic &&
          <section className="program-record-actions program-record-row justify-content-end">
            <Button
              label={gettext('Download Record')}
              className={['btn-primary']}
              onClick={this.downloadRecord}
            />
          </section>
        }

        <section className="program-record">
          <header className="d-flex justify-content-between program-record-header">
            <div className="program-overview">
              <h1 className="program-title h2">{ StringUtils.interpolate(gettext('{name} Record'), { name: program.name }) }</h1>
              <div className="text-muted program-type">
                <ProgramIcon type={program.type} className="program-icon" />
                { StringUtils.interpolate(gettext('{type} Program Record'), { type: program.type_name }) }
              </div>
              <div className="d-flex program-status">
                {program.completed ?
                  <span className="badge badge-success">{gettext('Earned')}</span>
                 :
                  <span className="badge badge-warning">{gettext('Partially Completed')}</span>
                }
                <span className="updated">
                  { StringUtils.interpolate(
                      gettext('Last Updated {date}'), {
                        date: this.formatDate(program.last_updated),
                      },
                    )
                  }
                </span>
              </div>
            </div>
            <div name="school-name" className="hd-3 school-name">
              { StringUtils.interpolate(gettext('{platform} | {school}'), { platform: platformName, school: program.school }) }
            </div>
          </header>

          <div className="learner-info">
            <h3 className="h4 font-weight-normal user">{learner.full_name}</h3>
            <div className="details">
              {learner.username}<span className="pipe">|</span>{learner.email}
            </div>
          </div>

          <div className="program-record-grades">
            <FoldingTable
              columns={[
                { key: 'name', label: gettext('Course Name') },
                { key: 'school', label: gettext('School') },
                { key: 'course_id', label: gettext('Course ID') },
                { key: 'percent_grade', label: gettext('Highest Grade Earned') },
                { key: 'letter_grade', label: gettext('Letter Grade') },
                { key: 'attempts', label: gettext('Verified Attempts') },
                { key: 'issue_date', label: gettext('Date Earned') },
                { key: 'status', label: gettext('Status') },
              ]}
              foldedColumns={[
                { key: 'name', className: 'hd-5 emphasized' },
                { key: 'school' },
                { key: 'course_id', format: gettext('Course ID: {}') },
                { key: 'percent_grade', format: gettext('Percent Grade: {}') },
                { key: 'letter_grade', format: gettext('Letter Grade: {}') },
                { key: 'attempts', format: gettext('Verified Attempts: {}') },
                { key: 'issue_date', format: gettext('Date Earned: {}') },
                { key: 'status', label: gettext('Status: {}') },
              ]}
              data={this.formatGradeData()}
              dataKey="name"
            />
          </div>
        </section>
        {sendRecordModalOpen &&
          <SendLearnerRecordModal
            {...defaultModalProps}
            onClose={this.closeSendRecordModal}
            uuid={uuid}
          />
        }
        {shareModelOpen &&
          <ShareProgramRecordModal
            {...defaultModalProps}
            onClose={this.closeShareModel}
            username={learner.username}
            uuid={uuid}
          />
        }
      </main>
    );
  }
}

ProgramRecord.propTypes = {
  learner: PropTypes.shape({
    email: PropTypes.string,
    full_name: PropTypes.string,
    username: PropTypes.string,
  }).isRequired,
  program: PropTypes.shape({
    name: PropTypes.string,
    school: PropTypes.string,
    completed: PropTypes.bool,
    type: PropTypes.string,
    type_name: PropTypes.string,
    last_updated: PropTypes.string,
  }).isRequired,
  grades: PropTypes.arrayOf(PropTypes.object).isRequired,
  isPublic: PropTypes.bool,
  uuid: PropTypes.string.isRequired,
  platform_name: PropTypes.string.isRequired,
  loadModalsAsChildren: PropTypes.bool,
};

ProgramRecord.defaultProps = {
  isPublic: true,
  loadModalsAsChildren: true,
};

export default ProgramRecord;
