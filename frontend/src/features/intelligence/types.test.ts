import { describe, expect, it } from 'vitest';

import type { DataQualitySection } from '@/features/intelligence/types';

describe('intelligence types', () => {
  it('accepts a minimal quality section shape', () => {
    const quality: DataQualitySection = {
      overall_score: 85,
      completeness: 90,
      consistency: 80,
      uniqueness: 95,
      validity: 88,
      integrity: 82,
      duplicate_percentage: 1,
      constant_columns: [],
      near_constant_columns: [],
      high_cardinality_columns: ['user_id'],
      issues: [],
      components: [],
    };
    expect(quality.overall_score).toBeGreaterThan(0);
  });
});
