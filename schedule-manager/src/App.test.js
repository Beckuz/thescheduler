import { render, screen } from '@testing-library/react';
import Calendar from './Components/Schedule.js';

test('renders learn react link', () => {
  render(<Calendar />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
