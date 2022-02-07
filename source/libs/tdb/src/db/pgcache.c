/*
 * Copyright (c) 2019 TAOS Data, Inc. <jhtao@taosdata.com>
 *
 * This program is free software: you can use, redistribute, and/or modify
 * it under the terms of the GNU Affero General Public License, version 3
 * or later ("AGPL"), as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */
#include "tdbInt.h"

typedef TD_DLIST_NODE(SPage) SPgListNode;
struct SPage {
  pgid_t      pgid;      // page id
  frame_id_t  frameid;   // frame id
  SPgListNode freeNode;  // for SPgCache.freeList
  uint8_t *   pData;     // real data
};

typedef TD_DLIST(SPage) SPgList;

struct SPgCache {
  SRWLatch mutex;
  pgsize_t pgsize;
  int32_t  npage;
  SPage *  pages;
  SPgList  freeList;
  struct {
    int32_t  nbucket;
    SPgList *buckets;
  } pght;  // page hash table
};

int pgCacheCreate(SPgCache **ppPgCache, pgsize_t pgSize, int32_t npage) {
  SPgCache *pPgCache;
  SPage *   pPage;

  *ppPgCache = NULL;

  if (!TDB_IS_PGSIZE_VLD(pgSize)) {
    return -1;
  }

  pPgCache = (SPgCache *)calloc(1, sizeof(*pPgCache));
  if (pPgCache == NULL) {
    return -1;
  }

  taosInitRWLatch(&(pPgCache->mutex));
  pPgCache->pgsize = pgSize;
  pPgCache->npage = npage;

  pPgCache->pages = (SPage *)calloc(npage, sizeof(SPage));
  if (pPgCache->pages == NULL) {
    pgCacheDestroy(pPgCache);
    return -1;
  }

  TD_DLIST_INIT(&(pPgCache->freeList));

  for (int32_t i = 0; i < npage; i++) {
    pPage = pPgCache->pages + i;

    pPage->pgid = TDB_IVLD_PGID;
    pPage->frameid = i;

    pPage->pData = (uint8_t *)calloc(1, pgSize);
    if (pPage->pData == NULL) {
      pgCacheDestroy(pPgCache);
      return -1;
    }

    pPgCache->pght.nbucket = npage;
    pPgCache->pght.buckets = (SPgList *)calloc(pPgCache->pght.nbucket, sizeof(SPgList));
    if (pPgCache->pght.buckets == NULL) {
      pgCacheDestroy(pPgCache);
      return -1;
    }

    TD_DLIST_APPEND_WITH_FIELD(&(pPgCache->freeList), pPage, freeNode);
  }

  *ppPgCache = pPgCache;
  return 0;
}

int pgCacheDestroy(SPgCache *pPgCache) {
  SPage *pPage;
  if (pPgCache) {
    tfree(pPgCache->pght.buckets);
    if (pPgCache->pages) {
      for (int32_t i = 0; i < pPgCache->npage; i++) {
        pPage = pPgCache->pages + i;
        tfree(pPage->pData);
      }

      free(pPgCache->pages);
    }
    free(pPgCache);
  }

  return 0;
}

int pgCacheOpen(SPgCache **ppPgCache) {
  if (*ppPgCache == NULL) {
    if (pgCacheCreate(ppPgCache, TDB_DEFAULT_PGSIZE, TDB_DEFAULT_CACHE_SIZE / TDB_DEFAULT_PGSIZE) < 0) {
      return -1;
    }
  }
  // TODO
  return 0;
}

int pgCacheClose(SPgCache *pPgCache) {
  // TODO
  return 0;
}

SPage *pgCacheFetch(SPgCache *pPgCache, pgid_t pgid) {
  SPage *pPage;

  // 1. Check if the page is cached
  return NULL;
}

int pgCacheRelease(SPage *pPage) {
  // TODO
  return 0;
}